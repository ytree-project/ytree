"""
save_arbor supporting functions



"""

import json
import numpy as np
import os

from yt.funcs import \
    ensure_dir, \
    get_pbar
from yt.frontends.ytdata.utilities import \
    save_as_dataset

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

def save_arbor(arbor, filename="arbor", fields=None, trees=None,
               max_file_size=524288):

    filename = determine_output_filename(filename, ".h5")
    fields = determine_field_list(arbor, fields)
    trees = determine_tree_list(arbor, trees)

    group_nnodes = []
    group_ntrees = []
    current_group = []
    cg_nnodes = 0
    cg_ntrees = 0

    root_field_data = dict((field, []) for field in fields)

    i = 1
    for tree in trees:
        current_group.append(tree)
        cg_nnodes += tree.tree_size
        cg_ntrees += 1
        if cg_nnodes > max_file_size:
            group_nnodes.append(cg_nnodes)
            group_ntrees.append(cg_ntrees)

            total_guess = int(np.round(arbor.size * i / sum(group_ntrees)))
            save_data_file(
                arbor, filename, fields,
                np.array(current_group), root_field_data,
                i, total_guess)

            current_group = []
            cg_nnodes = 0
            cg_ntrees = 0
            i += 1

    if cg_nnodes > 0:
        group_nnodes.append(cg_nnodes)
        group_ntrees.append(cg_ntrees)

    group_nnodes     = np.array(group_nnodes)
    group_ntrees     = np.array(group_ntrees)

    header_filename = save_header_file(
        arbor, filename, fields, root_field_data,
        group_nnodes, group_ntrees)
    return header_filename

def save_header_file(arbor, filename, fields, root_field_data,
                     group_nnodes, group_ntrees):
    """
    Write the header file.
    """

    ds = {}
    for attr in ["hubble_constant",
                 "omega_matter",
                 "omega_lambda"]:
        if hasattr(arbor, attr):
            ds[attr] = getattr(arbor, attr)
    extra_attrs = {"box_size": arbor.box_size,
                   "arbor_type": "YTreeArbor",
                   "unit_registry_json": arbor.unit_registry.to_json()}

    # write header file
    myfi = {}
    rdata = {}
    rtypes = {}
    fieldnames = get_output_fieldnames(fields)
    for field, fieldname in zip(fields, fieldnames):
        fi = arbor.field_info[field]
        myfi[fieldname] = \
          dict((key, fi[key])
               for key in ["units", "description"]
               if key in fi)
        rdata[fieldname] = np.concatenate(root_field_data[field])
        rtypes[fieldname] = "data"
    # all saved trees will be roots
    rdata["desc_uid"][:] = -1

    tree_end_index   = group_ntrees.cumsum()
    tree_start_index = tree_end_index - group_ntrees

    extra_attrs["field_info"] = json.dumps(myfi)
    extra_attrs["total_files"] = group_nnodes.size
    extra_attrs["total_trees"] = group_ntrees.sum()
    extra_attrs["total_nodes"] = group_nnodes.sum()
    hdata = {"tree_start_index": tree_start_index,
             "tree_end_index"  : tree_end_index,
             "tree_size"       : group_ntrees}
    hdata.update(rdata)
    del rdata
    htypes = dict((f, "index") for f in hdata)
    htypes.update(rtypes)

    header_filename = "%s.h5" % filename
    save_as_dataset(ds, header_filename, hdata,
                    field_types=htypes,
                    extra_attrs=extra_attrs)
    del hdata

    return header_filename

def determine_tree_list(arbor, trees):
    """
    Determine what trees are being saved.
    """

    if trees is None:
        trees = arbor.trees
    else:
        # assemble unique tree roots for getting fields
        trees = np.asarray(trees)
        roots = []
        root_uids = []
        for tree in trees:
            if tree.root == -1:
                my_root = tree
            else:
                my_root = tree.root
            if my_root.uid not in root_uids:
                roots.append(my_root)
                root_uids.append(my_root.uid)
        roots = np.array(roots)
        del root_uids

    return trees

def determine_output_filename(path, suffix):
    if path.endswith(suffix):
        dirname = os.path.dirname(path)
        filename = path[:-len(suffix)]
    else:
        dirname = path
        filename = os.path.join(
            dirname, os.path.basename(path))
    ensure_dir(dirname)
    return filename

def determine_field_list(arbor, fields):
    if fields in [None, "all"]:
        # If a field has an alias, get that instead.
        fields = []
        for field in arbor.field_list + arbor.analysis_field_list:
            fields.extend(
                arbor.field_info[field].get("aliases", [field]))
    else:
        fields.extend([f for f in ["uid", "desc_uid"]
                       if f not in fields])

    return fields


def get_output_fieldnames(fields):
    return [field.replace("/", "_") for field in fields]

def save_data_file(arbor, filename, fields, tree_group,
                   root_field_data,
                   current_iteration, total_guess):

    fieldnames = get_output_fieldnames(fields)
    ftypes = dict((f, "data") for f in fieldnames)

    arbor._node_io_loop(
        arbor._node_io.get_fields,
        pbar="Getting fields [%d / ~%d]" % (current_iteration, total_guess),
        root_nodes=tree_group, fields=fields, root_only=False)

    fdata = {}
    my_tree_size  = np.array([tree.tree_size for tree in tree_group])
    my_tree_end   = my_tree_size.cumsum()
    my_tree_start = my_tree_end - my_tree_size
    ntrees = my_tree_size.sum()
    pbar = get_pbar("Creating field arrays [%d / ~%d]" %
                    (current_iteration, total_guess),
                    len(fields)*ntrees)
    c = 0
    for field, fieldname in zip(fields, fieldnames):
        fdata[fieldname] = np.concatenate(
            [node._field_data[field] if node.is_root else node["tree", field]
             for node in tree_group])
        root_field_data[field].append(fdata[fieldname][my_tree_start])
        c += ntrees
        pbar.update(c)
    pbar.finish()

    # In case we have saved any non-root trees,
    # mark them as having no descendents.
    fdata['desc_uid'][my_tree_start] = -1

    pbar = get_pbar("Resetting trees", len(tree_group))
    for node in tree_group:
        node.reset()
        pbar.update(1)
    pbar.finish()

    fdata["tree_start_index"] = my_tree_start
    fdata["tree_end_index"]   = my_tree_end
    fdata["tree_size"]        = my_tree_size
    for ft in ["tree_start_index",
               "tree_end_index",
               "tree_size"]:
        ftypes[ft] = "index"
    my_filename = "%s_%04d.h5" % (filename, current_iteration-1)
    save_as_dataset({}, my_filename, fdata,
                    field_types=ftypes)
