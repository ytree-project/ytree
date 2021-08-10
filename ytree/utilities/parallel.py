"""
parallel utilities



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

from yt.funcs import is_root
from yt.utilities.parallel_tools.parallel_analysis_interface import \
    _get_comm, \
    parallel_objects, \
    parallel_root_only

def regenerate_node(arbor, node):
    """
    Regenerate the TreeNode using the provided arbor.

    This is to be used when the original arbor associated with the
    TreeNode no longer exists.
    """

    if node.is_root:
        return arbor[node._arbor_index]
    root_node = node.root
    return root_node.get_node("forest", node.tree_id)

def parallel_trees(trees, group="forest", save_every=None,
                   njobs=None, dynamic=None):
    arbor = trees[0].arbor
    fi = arbor.field_info
    afields = \
      [field for field in fi
       if fi[field].get("type") in ("analysis", "analysis_saved")]

    nt = len(trees)
    if save_every is None:
        nb = 1
    else:
        nb = int(np.ceil(nt / save_every))

    if njobs is None:
        comm = _get_comm(())
        # parallelize over trees if more trees than cores
        if nt > comm.size:
            njobs = (0, 1)
        else:
            njobs = (1, 0)
    else:
        if not isinstance(njobs, (tuple, list)) or len(njobs) != 2:
            raise ValueError(f"njobs must be a tuple of length 2: {njobs}.")

    if dynamic is None:
        dynamic = (False, False)
    else:
        if not isinstance(dynamic, (tuple, list)) or len(dynamic) != 2:
            raise ValueError(f"dynamic must be a tuple of length 2: {dynamic}.")

    for ib in range(nb):
        if save_every is None:
            start = 0
            end = nt
        else:
            start = ib * save_every
            end = min(start + save_every, nt)

        arbor_storage = {}
        for tree_store, itree in parallel_objects(
                range(start, end), storage=arbor_storage,
                njobs=njobs[0], dynamic=dynamic[0]):

            my_tree = trees[itree]
            my_halos = list(my_tree[group])

            tree_storage = {}
            for halo_store, ihalo in parallel_objects(
                    range(len(my_halos)), storage=tree_storage,
                    njobs=njobs[1], dynamic=dynamic[1]):

                my_halo = my_halos[ihalo]
                halo_store.result_id = my_halo.tree_id
                yield my_halo
                halo_store.result = {field: my_halo[field]
                                     for field in afields}

            # combine results for this tree
            if is_root():
                for tree_id, result in tree_storage.items():
                    my_halo = my_tree.get_node("forest", tree_id)

                    for field, value in result.items():
                        my_halo[field] = value

                tree_store.result = {field: my_tree["forest", field]
                                     for field in afields}
            else:
                tree_store.result_id = None

        # combine results for all trees
        if is_root():
            for i, my_tree in enumerate(trees):
                data = arbor_storage[i]
                for field in afields:
                    my_tree.field_data[field] = data[field]
            if save_every is not None:
                fn = arbor.save_arbor(trees=my_trees)
                arbor = ytree.load(fn)
                trees = [regenerate_node(arbor, tree) for tree in trees]
