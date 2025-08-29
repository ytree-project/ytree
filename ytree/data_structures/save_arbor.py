"""
save_arbor supporting functions



"""

import json
import numpy as np
import os
import types

from yt.frontends.ytdata.utilities import save_as_dataset
from yt.funcs import get_pbar
from ytree.utilities.io import ensure_dir
from ytree.utilities.logger import ytreeLogger as mylog

# -----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------


def save_arbor(
    arbor,
    filename=None,
    fields=None,
    trees=None,
    save_in_place=None,
    save_roots_only=False,
    max_file_size=524288,
):
    """
    Save the arbor to a file.

    This is the internal function called by Arbor.save_arbor.
    """

    from ytree.frontends.ytree.arbor import YTreeArbor

    is_ytree = isinstance(arbor, YTreeArbor)
    if save_in_place is None:
        save_in_place = is_ytree

    elif save_in_place and not is_ytree:
        raise ValueError(
            f"Cannot do save_in_place with arbor type {type(arbor)}. "
            "Resave full arbor first and then reload."
        )

    if not save_in_place and save_roots_only:
        raise ValueError("Cannot have save_in_place=False with save_roots_only=True")

    if isinstance(trees, types.GeneratorType):
        trees = list(trees)

    arbor._plant_trees()
    update, filename = determine_save_state(
        arbor, filename, fields, trees, save_in_place
    )
    filename = determine_output_filename(filename, ".h5")
    fields = determine_field_list(arbor, fields, update)

    if not fields:
        mylog.warning(
            "No action will be taken for the following reasons:\n"
            " - This dataset is already a YTreeArbor.\n"
            " - No filename has been given.\n"
            " - No new analysis fields have been created.\n"
            " - No custom list of trees has been provided."
        )
        return None

    group_nnodes, group_ntrees, root_field_data = save_data_files(
        arbor, filename, fields, trees, max_file_size, update, save_roots_only
    )

    header_filename = save_header_file(
        arbor, filename, fields, root_field_data, group_nnodes, group_ntrees
    )

    return header_filename


def determine_save_state(arbor, filename, fields, trees, in_place):
    """
    Determine if we can just output new analysis fields to
    sidecar files and skip saving the rest.

    If updating return filenames associated with currently loaded arbor.
    """

    from ytree.frontends.ytree.arbor import YTreeArbor

    fstate = (False, filename)
    tstate = (True, arbor.parameter_filename)

    if not isinstance(arbor, YTreeArbor):
        return fstate

    if filename is not None:
        return fstate

    if fields not in [None, "all"]:
        return fstate

    if not in_place and trees is not None:
        if len(trees) != arbor.size:
            return fstate

        my_uids = arbor.arr([t["uid"] for t in arbor])
        if (arbor["uid"] != my_uids).any():
            return fstate

    return tstate


def determine_output_filename(path, suffix):
    """
    Figure out the output filename.
    """

    if path is None:
        path = "arbor"

    if path.endswith(suffix):
        dirname = os.path.dirname(path)
        filename = path[: -len(suffix)]
    else:
        dirname = path
        filename = os.path.join(dirname, os.path.basename(path))
    ensure_dir(dirname)
    return filename


def determine_field_list(arbor, fields, update):
    """
    Get the list of fields to be saved.
    """

    if fields in [None, "all"]:
        # If this is an update, don't resave disk fields.
        field_list = set(arbor.analysis_field_list)

        # If not an update, save all the fields.
        if not update:
            field_list.update(arbor.field_list)

        # If a field has an alias, get that instead.
        fields = []
        for field in field_list:
            fields.extend(arbor.field_info[field].get("aliases", [field]))

    else:
        # If not saving all trees, add uid and desc_uid fields
        # to make sure the tree can be built.
        fields = list(set(fields + ["uid", "desc_uid"]))

    return fields


def get_output_fieldnames(fields):
    """
    Get filenames as they will be written to disk.
    """

    return [field.replace("/", "_") for field in fields]


def save_data_files(arbor, filename, fields, trees, max_file_size, update, nodes_only):
    """
    Write all data files by grouping trees together.

    Return arrays of number of nodes and trees written to each file
    as well as a dictionary of root fields.

    If update is True, use the file layout of the arbor instead of
    calculating from max_file_size.
    """

    # Keep the trees we want to transplant separate.
    if trees is not None and update:
        save_trees = trees

    if trees is None or update:
        trees = arbor._yield_root_nodes(range(arbor.size))
        save_size = arbor.size
    else:
        save_size = len(trees)

    if update:
        # Transplant field data onto tree roots.
        save_roots = transplant_analysis_fields(arbor, save_trees, nodes_only)
        # If we have new analysis fields, they must be written for
        # the entire arbor.
        save_all = any(
            [arbor.field_info[field]["type"] == "analysis" for field in fields]
        )
        file_sizes = np.diff(arbor._node_io._ei, prepend=0)
    else:
        save_roots = {}
        save_all = True

    # This is the set of files we need to save.
    if not save_all:
        save_files = set(
            np.digitize([tree._ai for tree in save_roots.values()], arbor._node_io._ei)
        )

    root_field_data = {field: [] for field in fields}

    group_nnodes = []
    group_ntrees = []
    current_group = []
    cg_nnodes = 0
    cg_ntrees = 0

    def my_save(cg_number, cg_nnodes, cg_ntrees):
        group_nnodes.append(cg_nnodes)
        group_ntrees.append(cg_ntrees)

        if update:
            total_guess = file_sizes.size
        else:
            total_guess = int(np.round(save_size * (cg_number + 1) / sum(group_ntrees)))

        # If we don't need to save the data file, just gather root fields.
        if not save_all and cg_number not in save_files:
            mylog.info(f"[{cg_number + 1}] / [~{total_guess}]: Compiling root fields.")
            cg_start = current_group[0]._arbor_index
            cg_end = current_group[-1]._arbor_index + 1
            for field in fields:
                root_field_data[field].append(arbor[field][cg_start:cg_end])

        else:
            save_data_file(
                arbor,
                filename,
                fields,
                np.array(current_group),
                root_field_data,
                cg_number,
                total_guess,
            )

    i = 0
    for tree in trees:
        if update:
            tree = save_roots.get(tree._arbor_index, tree)

        current_group.append(tree)
        cg_nnodes += tree.tree_size
        cg_ntrees += 1

        # if updating, use file sizes of loaded arbor
        if (
            update and len(current_group) == file_sizes[i]
        ) or cg_nnodes > max_file_size:
            my_save(i, cg_nnodes, cg_ntrees)
            current_group = []
            cg_nnodes = 0
            cg_ntrees = 0
            i += 1

    if current_group:
        my_save(i, cg_nnodes, cg_ntrees)

    group_nnodes = np.array(group_nnodes)
    group_ntrees = np.array(group_ntrees)

    return group_nnodes, group_ntrees, root_field_data


def save_data_file(
    arbor, filename, fields, tree_group, root_field_data, current_iteration, total_guess
):
    """
    Write data file for a single group of trees.
    """

    fieldnames = get_output_fieldnames(fields)

    arbor._node_io_loop(
        arbor._node_io.get_fields,
        pbar=f"Getting fields [{current_iteration + 1} / ~{total_guess}]",
        root_nodes=tree_group,
        fields=fields,
        root_only=False,
    )

    main_fdata = {}
    main_ftypes = {}

    analysis_fdata = {}
    analysis_ftypes = {}

    my_tree_size = np.array([tree.tree_size for tree in tree_group])
    my_tree_end = my_tree_size.cumsum()
    my_tree_start = my_tree_end - my_tree_size
    for field, fieldname in zip(fields, fieldnames):
        fi = arbor.field_info[field]

        if fi.get("type") in ["analysis", "analysis_saved"]:
            my_fdata = analysis_fdata
            my_ftypes = analysis_ftypes
        else:
            my_fdata = main_fdata
            my_ftypes = main_ftypes

        my_ftypes[fieldname] = "data"
        my_fdata[fieldname] = np.concatenate(
            [
                node.field_data[field] if node.is_root else node["tree", field]
                for node in tree_group
            ]
        )
        root_field_data[field].append(my_fdata[fieldname][my_tree_start])

    # In case we have saved any non-root trees,
    # mark them as having no descendents.
    if "desc_uid" in main_fdata:
        main_fdata["desc_uid"][my_tree_start] = -1

    for node in tree_group:
        arbor.reset_node(node)

    if main_fdata:
        main_fdata["tree_start_index"] = my_tree_start
        main_fdata["tree_end_index"] = my_tree_end
        main_fdata["tree_size"] = my_tree_size
        for ft in ["tree_start_index", "tree_end_index", "tree_size"]:
            main_ftypes[ft] = "index"
        my_filename = f"{filename}_{current_iteration:04d}.h5"
        save_as_dataset({}, my_filename, main_fdata, field_types=main_ftypes)

    if analysis_fdata:
        my_filename = f"{filename}_{current_iteration:04d}-analysis.h5"
        save_as_dataset({}, my_filename, analysis_fdata, field_types=analysis_ftypes)


def save_header_file(
    arbor, filename, fields, root_field_data, group_nnodes, group_ntrees
):
    """
    Write the header file.
    """

    ds = {}
    for attr in ["hubble_constant", "omega_matter", "omega_lambda"]:
        if getattr(arbor, attr, None) is not None:
            ds[attr] = getattr(arbor, attr)

    # Data structures for disk fields.
    main_fi = {}
    main_rdata = {}
    main_rtypes = {}

    # Analysis fields saved separately.
    analysis_fi = {}
    analysis_rdata = {}
    analysis_rtypes = {}

    fieldnames = get_output_fieldnames(fields)
    for field, fieldname in zip(fields, fieldnames):
        fi = arbor.field_info[field]

        if fi.get("type") in ["analysis", "analysis_saved"]:
            my_fi = analysis_fi
            my_rdata = analysis_rdata
            my_rtypes = analysis_rtypes
        else:
            my_fi = main_fi
            my_rdata = main_rdata
            my_rtypes = main_rtypes

        my_fi[fieldname] = dict(
            (key, fi[key]) for key in ["units", "description"] if key in fi
        )
        my_rdata[fieldname] = np.concatenate(root_field_data[field])
        my_rtypes[fieldname] = "data"

    # all saved trees will be roots
    if "desc_uid" in main_rdata:
        main_rdata["desc_uid"][:] = -1

    # Save the primary fields.
    header_filename = f"{filename}.h5"
    if main_fi:
        tree_end_index = group_ntrees.cumsum()
        tree_start_index = tree_end_index - group_ntrees

        extra_attrs = {
            "arbor_type": "YTreeArbor",
            "unit_registry_json": arbor.unit_registry.to_json(),
            "unit_system_name": arbor.unit_registry.unit_system.name,
        }
        if arbor.box_size is not None:
            extra_attrs["box_size"] = arbor.box_size
        extra_attrs["field_info"] = json.dumps(main_fi)
        extra_attrs["total_files"] = group_nnodes.size
        extra_attrs["total_trees"] = group_ntrees.sum()
        extra_attrs["total_nodes"] = group_nnodes.sum()
        hdata = {
            "tree_start_index": tree_start_index,
            "tree_end_index": tree_end_index,
            "tree_size": group_ntrees,
        }
        hdata.update(main_rdata)
        del main_rdata
        htypes = dict((f, "index") for f in hdata)
        htypes.update(main_rtypes)

        save_as_dataset(
            ds, header_filename, hdata, field_types=htypes, extra_attrs=extra_attrs
        )
        del hdata

    # Save analysis fields to a sidecar file.
    if analysis_fi:
        extra_attrs = {}
        extra_attrs["field_info"] = json.dumps(analysis_fi)
        hdata = analysis_rdata
        del analysis_rdata
        htypes = dict((f, "index") for f in hdata)
        htypes.update(analysis_rtypes)

        analysis_header_filename = f"{filename}-analysis.h5"
        save_as_dataset(
            ds,
            analysis_header_filename,
            hdata,
            field_types=htypes,
            extra_attrs=extra_attrs,
        )
        del hdata

    return header_filename


def transplant_analysis_fields(arbor, old_trees, nodes_only):
    """
    Copy analysis field data from one set of trees to another.

    The new tree list is likely to be the list of all trees in the arbor.
    The purpose of this is to allow saving in place of a subset of trees
    (including non-rootes) back into the original arbor.
    """

    root_ids = {}

    pbar = get_pbar("Transplanting analysis fields", len(old_trees))
    for i, old_tree in enumerate(old_trees):
        old_root = old_tree.find_root()
        ai = old_root._arbor_index
        if ai in root_ids:
            new_root = root_ids[ai]
        else:
            new_root = arbor[ai]
            root_ids[ai] = new_root

        if nodes_only:
            indices = old_tree.tree_id
        elif old_tree.is_root:
            indices = slice(None)
        else:
            indices = old_tree._tree_field_indices

        arbor._node_io.get_fields(new_root, fields=arbor.analysis_field_list)
        for field in arbor.analysis_field_list:
            if nodes_only:
                my_field = field
            elif old_tree.is_root:
                my_field = ("forest", field)
            else:
                my_field = ("tree", field)
            new_root.field_data[field][indices] = old_tree[my_field]

        pbar.update(i + 1)
    pbar.finish()

    return root_ids
