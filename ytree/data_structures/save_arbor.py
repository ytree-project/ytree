"""
save_arbor supporting functions



"""

import json
import numpy as np
import os
import types
from unyt import uconcatenate

from yt.frontends.ytdata.utilities import save_as_dataset
from ytree.utilities.io import ensure_dir
from ytree.utilities.logger import ytreeLogger as mylog

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

def save_arbor(arbor, filename=None, fields=None, trees=None,
               max_file_size=524288):
    """
    Save the arbor to a file.

    This is the internal function called by Arbor.save_arbor.
    """

    if isinstance(trees, types.GeneratorType):
        trees = list(trees)

    arbor._plant_trees()
    update, filename = determine_save_state(
        arbor, filename, fields, trees)
    filename = determine_output_filename(filename, ".h5")
    fields = determine_field_list(arbor, fields, update)

    if not fields:
        mylog.warning(
            "No action will be taken for the following reasons:\n"
            " - This dataset is already a YTreeArbor.\n"
            " - No filename has been given.\n"
            " - No new analysis fields have been created.\n"
            " - No custom list of trees has been provided.")
        return None

    group_nnodes, group_ntrees, root_field_data = \
      save_data_files(arbor, filename, fields, trees,
                      max_file_size, update)

    header_filename = save_header_file(
        arbor, filename, fields, root_field_data,
        group_nnodes, group_ntrees)

    return header_filename

def determine_save_state(arbor, filename, fields, trees):
    """
    Determine if we can just output new analysis fields to
    sidecar files and skip saving the rest.

    If updating return filenames associated with currently loaded arbor.
    """

    from ytree.frontends.ytree.arbor import YTreeArbor

    if not isinstance(arbor, YTreeArbor):
        return False, filename

    if filename is not None:
        return False, filename

    if fields not in [None, "all"]:
        return False, filename

    if trees is not None and len(trees) != arbor.size:
        return False, filename

    return True, arbor.parameter_filename

def determine_output_filename(path, suffix):
    """
    Figure out the output filename.
    """

    if path is None:
        path = 'arbor'

    if path.endswith(suffix):
        dirname = os.path.dirname(path)
        filename = path[:-len(suffix)]
    else:
        dirname = path
        filename = os.path.join(
            dirname, os.path.basename(path))
    ensure_dir(dirname)
    return filename

def determine_field_list(arbor, fields, update):
    """
    Get the list of fields to be saved.
    """

    if fields in [None, "all"]:
        # If this is an update, don't resave disk fields.
        field_list = arbor.analysis_field_list.copy()

        # Add in previously saved analysis fields
        if update:
            field_list.extend(
                [field for field in arbor.field_list
                 if arbor.field_info[field].get("type") == "analysis_saved"])
        else:
            field_list.extend(arbor.field_list)

        # If a field has an alias, get that instead.
        fields = []
        for field in field_list:
            fields.extend(
                arbor.field_info[field].get("aliases", [field]))

    else:
        fields.extend([f for f in ["uid", "desc_uid"]
                       if f not in fields])

    return fields

def get_output_fieldnames(fields):
    """
    Get filenames as they will be written to disk.
    """

    return [field.replace("/", "_") for field in fields]

def save_data_files(arbor, filename, fields, trees,
                    max_file_size, update):
    """
    Write all data files by grouping trees together.

    Return arrays of number of nodes and trees written to each file
    as well as a dictionary of root fields.

    If update is True, use the file layout of the arbor instead of
    calculating from max_file_size.
    """

    if trees is None:
        trees = arbor._yield_root_nodes(range(arbor.size))
        save_size = arbor.size
    else:
        save_size = len(trees)

    root_field_data = dict((field, []) for field in fields)

    group_nnodes = []
    group_ntrees = []
    current_group = []
    cg_nnodes = 0
    cg_ntrees = 0

    def my_save(cg_number, cg_nnodes, cg_ntrees):
        group_nnodes.append(cg_nnodes)
        group_ntrees.append(cg_ntrees)

        total_guess = int(np.round(save_size * cg_number / sum(group_ntrees)))
        save_data_file(
            arbor, filename, fields,
            np.array(current_group), root_field_data,
            cg_number, total_guess)

    if update:
        file_sizes = np.diff(arbor._node_io._ei, prepend=0)

    i = 1
    for tree in trees:
        current_group.append(tree)
        cg_nnodes += tree.tree_size
        cg_ntrees += 1

        # if updating, use file sizes of loaded arbor
        if (update and len(current_group) == file_sizes[i-1]) or \
          cg_nnodes > max_file_size:
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

def save_data_file(arbor, filename, fields, tree_group,
                   root_field_data,
                   current_iteration, total_guess):
    """
    Write data file for a single group of trees.
    """

    fieldnames = get_output_fieldnames(fields)

    arbor._node_io_loop(
        arbor._node_io.get_fields,
        pbar=f"Getting fields [{current_iteration} / ~{total_guess}]",
        root_nodes=tree_group, fields=fields, root_only=False)

    main_fdata  = {}
    main_ftypes = {}

    analysis_fdata  = {}
    analysis_ftypes = {}

    my_tree_size  = np.array([tree.tree_size for tree in tree_group])
    my_tree_end   = my_tree_size.cumsum()
    my_tree_start = my_tree_end - my_tree_size
    for field, fieldname in zip(fields, fieldnames):
        fi = arbor.field_info[field]

        if fi.get("type") in ["analysis", "analysis_saved"]:
            my_fdata  = analysis_fdata
            my_ftypes = analysis_ftypes
        else:
            my_fdata  = main_fdata
            my_ftypes = main_ftypes

        my_ftypes[fieldname] = "data"
        my_fdata[fieldname]  = uconcatenate(
            [node.field_data[field] if node.is_root else node["tree", field]
             for node in tree_group])
        root_field_data[field].append(my_fdata[fieldname][my_tree_start])

    # In case we have saved any non-root trees,
    # mark them as having no descendents.
    if "desc_uid" in main_fdata:
        main_fdata["desc_uid"][my_tree_start] = -1

    for node in tree_group:
        arbor.reset_node(node)

    if main_fdata:
        main_fdata["tree_start_index"] = my_tree_start
        main_fdata["tree_end_index"]   = my_tree_end
        main_fdata["tree_size"]        = my_tree_size
        for ft in ["tree_start_index",
                   "tree_end_index",
                   "tree_size"]:
            main_ftypes[ft] = "index"
        my_filename = f"{filename}_{current_iteration-1:04d}.h5"
        save_as_dataset({}, my_filename, main_fdata,
                        field_types=main_ftypes)

    if analysis_fdata:
        my_filename = f"{filename}_{current_iteration-1:04d}-analysis.h5"
        save_as_dataset({}, my_filename, analysis_fdata,
                        field_types=analysis_ftypes)

def save_header_file(arbor, filename, fields, root_field_data,
                     group_nnodes, group_ntrees):
    """
    Write the header file.
    """

    ds = {}
    for attr in ["hubble_constant",
                 "omega_matter",
                 "omega_lambda"]:
        if getattr(arbor, attr, None) is not None:
            ds[attr] = getattr(arbor, attr)

    # Data structures for disk fields.
    main_fi     = {}
    main_rdata  = {}
    main_rtypes = {}

    # Analysis fields saved separately.
    analysis_fi     = {}
    analysis_rdata  = {}
    analysis_rtypes = {}

    fieldnames = get_output_fieldnames(fields)
    for field, fieldname in zip(fields, fieldnames):
        fi = arbor.field_info[field]

        if fi.get("type") in ["analysis", "analysis_saved"]:
            my_fi     = analysis_fi
            my_rdata  = analysis_rdata
            my_rtypes = analysis_rtypes
        else:
            my_fi     = main_fi
            my_rdata  = main_rdata
            my_rtypes = main_rtypes

        my_fi[fieldname] = \
          dict((key, fi[key])
               for key in ["units", "description"]
               if key in fi)
        my_rdata[fieldname] = uconcatenate(root_field_data[field])
        my_rtypes[fieldname] = "data"

    # all saved trees will be roots
    if "desc_uid" in main_rdata:
        main_rdata["desc_uid"][:] = -1

    # Save the primary fields.
    header_filename = f"{filename}.h5"
    if main_fi:
        tree_end_index   = group_ntrees.cumsum()
        tree_start_index = tree_end_index - group_ntrees

        extra_attrs = {
            "arbor_type": "YTreeArbor",
            "unit_registry_json": arbor.unit_registry.to_json(),
            "unit_system_name": arbor.unit_registry.unit_system.name}
        if arbor.box_size is not None:
            extra_attrs["box_size"] = arbor.box_size
        extra_attrs["field_info"] = json.dumps(main_fi)
        extra_attrs["total_files"] = group_nnodes.size
        extra_attrs["total_trees"] = group_ntrees.sum()
        extra_attrs["total_nodes"] = group_nnodes.sum()
        hdata = {"tree_start_index": tree_start_index,
                 "tree_end_index"  : tree_end_index,
                 "tree_size"       : group_ntrees}
        hdata.update(main_rdata)
        del main_rdata
        htypes = dict((f, "index") for f in hdata)
        htypes.update(main_rtypes)

        save_as_dataset(ds, header_filename, hdata,
                        field_types=htypes,
                        extra_attrs=extra_attrs)
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
        save_as_dataset(ds, analysis_header_filename, hdata,
                        field_types=htypes,
                        extra_attrs=extra_attrs)
        del hdata

    return header_filename
