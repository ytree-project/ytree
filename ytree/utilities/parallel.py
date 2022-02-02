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

import numpy as np

from yt.funcs import is_root
from yt.utilities.parallel_tools.parallel_analysis_interface import \
    _get_comm, \
    parallel_objects

from ytree.data_structures.load import load as ytree_load

def regenerate_node(arbor, node, new_index=None):
    """
    Regenerate the TreeNode using the provided arbor.

    This is to be used when the original arbor associated with the
    TreeNode no longer exists.

    If new_index is None, assume the arbor has the same structure
    as it did before. If new_index is not None, assume the node
    is now a root.
    """

    if new_index is None:
        root_node = node.find_root()
        new_node = root_node.get_node("forest", node.tree_id)
    else:
        root_node = arbor[new_index]
        new_node = root_node

    return new_node

def _get_analysis_fields(arbor):
    fi = arbor.field_info
    return [field for field in fi
            if fi[field].get("type") in ("analysis", "analysis_saved")]

def parallel_trees(trees, save_every=None, filename=None,
                   njobs=0, dynamic=False):
    """
    Iterate over a list of trees in parallel.

    Trees are divided up between the available processor groups. Analysis
    field values can then be assigned to halos within the tree. The trees
    will be saved either at the end of the loop or after a number of trees
    given by the ``save_every`` keyword are completed.

    This uses the yt
    :func:`~yt.utilities.parallel_tools.parallel_analysis_interface.parallel_objects`
    function, which is parallelized with MPI underneath and so is suitable
    for parallelism across compute nodes.

    Parameters
    ----------
    trees : list of :class:`~ytree.data_structures.tree_node.TreeNode` objects
        The trees to be iterated over in parallel.
    save_every : optional, int or False
        Number of trees to be completed before results are saved. This is
        used to save intermediate results in case scripts need to be restarted.
        If None, save will only occur after iterating over all trees. If False,
        no saving will be done.
        Default: None
    filename : optional, string
        The name of the new arbor to be saved. If None, the naming convention
        will follow the filename keyword of the
        :func:`~ytree.data_structures.arbor.Arbor.save_arbor` function.
        Default: None
    njobs : optional, int
        The number of process groups for parallel iteration. Set to 0 to make
        the same number of process groups as available processors. Hence,
        each tree will be allocated to a single processor. Set to a number
        less than the total number of processors to create groups with multiple
        processors, which will allow for further parallelization within a tree.
        For example, running with 8 processors and setting njobs to 4 will result
        in 4 groups of 2 processors each.
        Default: 0
    dynamic : optional, bool
        Set to False to divide iterations evenly among process groups. Set to
        True to allocate iterations with a task queue. If True, the number of
        processors available will be one fewer than the total as one will act
        as the task queue server.
        Default: False

    Examples
    --------

    >>> import ytree
    >>> a = ytree.load("arbor/arbor.h5")
    >>> a.add_analysis_field("test_field", default=-1, units="Msun")
    >>> trees = list(a[:])
    >>> for tree in ytree.parallel_trees(trees):
    ...     for node in tree["forest"]:
    ...         node["test_field"] = 2 * node["mass"] # some analysis

    See Also
    --------
    parallel_tree_nodes, parallel_nodes

    """

    arbor = trees[0].arbor
    afields = _get_analysis_fields(arbor)

    nt = len(trees)
    save = True
    if save_every is None:
        save_every = nt
    elif save_every is False:
        save_every = nt
        save = False
    nb = int(np.ceil(nt / save_every))

    for ib in range(nb):
        start = ib * save_every
        end = min(start + save_every, nt)

        arbor_storage = {}
        for tree_store, itree in parallel_objects(
                range(start, end), storage=arbor_storage,
                njobs=njobs, dynamic=dynamic):

            my_tree = trees[itree]
            yield my_tree

            if is_root():
                my_root = my_tree.find_root()
                tree_store.result_id = (my_root._arbor_index, my_tree.tree_id)

                # If the tree is not a root, only save the "tree" selection
                # as we could overwrite other trees in the forest.
                if my_tree.is_root:
                    selection = "forest"
                else:
                    selection = "tree"

                tree_store.result = {field: my_tree[selection, field]
                                     for field in afields}

            else:
                tree_store.result_id = None

        # combine results for all trees
        if is_root():
            for itree in range(start, end):
                my_tree = trees[itree]
                my_root = my_tree.find_root()
                key = (my_root._arbor_index, my_tree.tree_id)
                data = arbor_storage[key]

                if my_tree.is_root:
                    indices = slice(None)
                else:
                    indices = [my_tree._tree_field_indices]

                for field in afields:
                    if field not in my_root.field_data:
                        arbor._node_io._initialize_analysis_field(my_root, field)
                    my_root.field_data[field][indices] = data[field]

            if save:
                fn = arbor.save_arbor(filename=filename, trees=trees)
                arbor = ytree_load(fn)
                trees = [regenerate_node(arbor, tree, new_index=i)
                         for i, tree in enumerate(trees)]

def parallel_tree_nodes(tree, group="forest",
                        njobs=0, dynamic=False):
    """
    Iterate over nodes in a single tree in parallel.

    Nodes are divided up between the available processor groups. Analysis
    field values can then be assigned to each node (halo).

    Note, unlike the parallel_trees and parallel_nodes function, no saving
    is performed internally. Results saving with the
    :func:`~ytree.data_structures.arbor.Arbor.save_arbor` must be done
    manually.

    This uses the yt
    :func:`~yt.utilities.parallel_tools.parallel_analysis_interface.parallel_objects`
    function, which is parallelized with MPI underneath and so is suitable
    for parallelism across compute nodes.

    Parameters
    ----------
    tree : :class:`~ytree.data_structures.tree_node.TreeNode`
        The tree whose nodes will be iterated over.
    group : optional, str ("forest", "tree", or "prog")
        Determines the nodes to be iterated over in the tree: "forest" for
        all nodes in the forest, "tree" for all nodes in the tree, or "prog"
        for all nodes in the line of main progenitors.
        Default: "forest"
    njobs : optional, int
        The number of process groups for parallel iteration. Set to 0 to make
        the same number of process groups as available processors. Hence,
        each node will be allocated to a single processor. Set to a number
        less than the total number of processors to create groups with multiple
        processors, which will allow for further parallelization. For example,
        running with 8 processors and setting njobs to 4 will result in 4
        groups of 2 processors each.
        Default: 0
    dynamic : optional, bool
        Set to False to divide iterations evenly among process groups. Set to
        True to allocate iterations with a task queue. If True, the number of
        processors available will be one fewer than the total as one will act
        as the task queue server.
        Default: False

    Examples
    --------

    >>> import ytree
    >>> a = ytree.load("arbor/arbor.h5")
    >>> a.add_analysis_field("test_field", default=-1, units="Msun")
    >>> trees = list(a[:])
    >>> for tree in trees:
    ...     for node in ytree.parallel_tree_nodes(tree):
    ...         node["test_field"] = 2 * node["mass"] # some analysis

    See Also
    --------
    parallel_trees, parallel_nodes

    """

    afields = _get_analysis_fields(tree.arbor)

    my_halos = list(tree[group])

    tree_storage = {}
    for halo_store, ihalo in parallel_objects(
            range(len(my_halos)), storage=tree_storage,
            njobs=njobs, dynamic=dynamic):

        my_halo = my_halos[ihalo]
        yield my_halo
        if is_root():
            halo_store.result_id = my_halo.tree_id
            halo_store.result = {field: my_halo[field]
                                 for field in afields}
        else:
            halo_store.result_id = -1

    # combine results for this tree
    if is_root():
        for tree_id, result in sorted(tree_storage.items()):
            if tree_id == -1:
                continue
            my_halo = tree.get_node("forest", tree_id)

            for field, value in result.items():
                my_halo[field] = value

def parallel_nodes(trees, group="forest", save_every=None,
                   filename=None, njobs=None, dynamic=None):
    """
    Iterate over all nodes in a list of trees in parallel.

    Both trees and/or nodes within a tree are divided up between available
    process groups using multi-level parallelism. Analysis field values can
    then be assigned to all nodes (halos). Trees will be saved either at the
    end of the loop over all trees or after a number of trees given by the
    ``save_every`` keyword are completed.

    This uses the yt
    :func:`~yt.utilities.parallel_tools.parallel_analysis_interface.parallel_objects`
    function, which is parallelized with MPI underneath and so is suitable
    for parallelism across compute nodes.

    Parameters
    ----------
    trees : list of :class:`~ytree.data_structures.tree_node.TreeNode` objects
        The trees to be iterated over in parallel.
    group : optional, str ("forest", "tree", or "prog")
        Determines the nodes to be iterated over in the tree: "forest" for
        all nodes in the forest, "tree" for all nodes in the tree, or "prog"
        for all nodes in the line of main progenitors.
        Default: "forest"
    save_every : optional, int or False
        Number of trees to be completed before results are saved. This is
        used to save intermediate results in case scripts need to be restarted.
        If None, save will only occur after iterating over all trees. If False,
        no saving will be done.
        Default: None
    filename : optional, string
        The name of the new arbor to be saved. If None, the naming convention
        will follow the filename keyword of the
        :func:`~ytree.data_structures.arbor.Arbor.save_arbor` function.
        Default: None
    njobs : optional, tuple of ints
        The number of process groups for parallel iteration over trees and
        nodes within each tree. The first value sets behavior for iteration
        over trees and the second for iteration over nodes in a tree. For
        example, set to (1, 0) to parallelize only over nodes in a tree and
        (0, 1) to parallelize only over trees. For multi-level parallelism
        set the first value to a number less than the total number of
        processors and the second to 0. For example, if running with 8
        processors, set njobs to (2, 0) to iterate over each tree with a
        group of 4 processors. Within each tree, each of the 4 processors
        in the group will work on a single node. If set to None, njobs will
        be set to (0, 1) if there are most trees than processors (tree
        parallel) and (1, 0) otherwise (node parallel).
        Default: None
    dynamic : optional, tuples of bools
        Toggles task queue on/off for parallelism over trees (first value)
        and nodes within a tree (second). Set to a value False to divide
        iterations evenly among process groups. Set to True to allocate
        iterations with a task queue. If True, the number of
        processors available will be one fewer than the total as one will
        act as the task queue server. Yes, this can be set to (True, True).
        Try it.
        Default: (False, False)

    Examples
    --------

    >>> import ytree
    >>> a = ytree.load("arbor/arbor.h5")
    >>> a.add_analysis_field("test_field", default=-1, units="Msun")
    >>> trees = list(a[:])
    >>> for node in ytree.parallel_nodes(trees):
    ...     node["test_field"] = 2 * node["mass"] # some analysis

    See Also
    --------
    parallel_trees, parallel_tree_nodes

    """

    if njobs is None:
        comm = _get_comm(())
        # parallelize over trees if more trees than cores
        if len(trees) > comm.size:
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

    for tree in parallel_trees(
            trees, save_every=save_every, filename=filename,
            njobs=njobs[0], dynamic=dynamic[0]):

        for node in parallel_tree_nodes(
                tree, group=group,
                njobs=njobs[1], dynamic=dynamic[1]):

            yield node
