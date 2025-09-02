"""
parallel utilities



"""

# -----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------

import numpy as np

from yt.funcs import get_pbar, is_root as yt_is_root
from yt.utilities.parallel_tools.parallel_analysis_interface import (
    _get_comm,
    parallel_objects,
)

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


def parallel_trees(
    trees,
    collect_results=True,
    save_every=None,
    save_in_place=None,
    save_roots_only=False,
    filename=None,
    njobs=0,
    dynamic=False,
):
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
    collect_results : optional, bool
        If True, then results stored in analysis fields will be collected
        by the root process. This must be set to True if saving is to be
        done. If False, results collection is ignored. This will result in
        a significant speedup. If you have no intention of altering analysis
        fields or do not need results to be recollected or saved, then this is
        the best option. Setting this to False will automatically set
        save_every to False as well.
        Default: True
    save_every : optional, int or False
        Number of trees to be completed before results are saved. This is used to
        save intermediate results in case scripts need to be restarted. This
        parameter results in different behavior depending on the value of the
        collect_results keyword. If save_every is set to:

            - integer: if collect_trees is True, the number of trees to complete
              before saving. If collect_trees is False, a ValueError exception will
              be raised.
            - False: no saving will be done. Results will still be collected if
              collect_results is True.
            - None: if collect_results if True, save will occur after iterating over
              all trees. If collect_results is False, no saving will be done.

        Default: None
    save_in_place : optional, bool or None
        If True, analysis fields will be saved to the original
        arbor, even if only a subset of all trees is provided
        with the trees keyword. If False and only a subset of
        all trees is provided, a new arbor will be created
        containing only the trees provided. If set to None,
        behavior is determined by the type of arbor loaded.
        If the arbor is a YTreeArbor (i.e., saved with
        save_arbor), save_in_place will be set to True. If
        not of this type, it will be set to False.
        Default: None
    save_roots_only : optional, bool
        If True, only field values of each node are saved.
        If False, field data for the entire tree stemming
        from that node are saved.
        Default:  False.
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

    comm = _get_comm(())
    # This is the root process of the whole operation.
    # We may split into process groups later, in which case there
    # will be other root processes and we will uses calls to yt's
    # is_root to identify them.
    is_global_root = comm.comm is None or comm.comm.rank == 0

    if dynamic:
        if is_global_root:
            nt = len(trees)
        else:
            nt = None
        nt = comm.mpi_bcast(nt, root=0)
    else:
        nt = len(trees)

    if nt < 1:
        return

    arbor = trees[0].arbor
    afields = arbor.analysis_field_list

    if save_in_place is None:
        from ytree.frontends.ytree.arbor import YTreeArbor

        save_in_place = isinstance(arbor, YTreeArbor)

    # are we actually going to save anything?
    do_save = True
    if isinstance(save_every, (int, np.integer)):
        if collect_results is False:
            raise ValueError(
                "collect_results must be True if save_every is set to a number."
            )
    elif save_every is False:
        save_every = nt
        do_save = False
    elif save_every is None:
        do_save = collect_results
        save_every = nt
    nb = int(np.ceil(nt / save_every))

    for ib in range(nb):
        start = ib * save_every
        end = min(start + save_every, nt)

        my_items = range(start, end)

        arbor_storage = {}
        for tree_store, my_item in parallel_objects(
            my_items, storage=arbor_storage, njobs=njobs, dynamic=dynamic
        ):
            my_tree = trees[my_item]
            yield my_tree

            # We use yt_is_root here because we want the root of this
            # workgroup running this iteration, not the global root.
            # It is this process's job to round up the results for this
            # iteration and place them in the storage object. This is the
            # the slowest part as we will copy field data for all of the
            # analysis fields for the entire forest or tree. In the future,
            # it may be worth trying to identify the nodes and analysis fields
            # which were actually altered and copying just them.
            if yt_is_root():
                if not collect_results:
                    continue

                # this is fast
                my_root = my_tree.find_root()

                tree_store.result_id = (my_root._arbor_index, my_tree.tree_id)

                # If the tree is not a root, only save the "tree" selection
                # as we could overwrite other trees in the forest.
                if save_roots_only:
                    pass
                elif my_tree.is_root:
                    selection = "forest"
                else:
                    selection = "tree"

                if save_roots_only:
                    tree_store.result = {field: my_tree[field] for field in afields}
                else:
                    # this is the slow part as we are grabbing all analysis
                    # fields for the entire tree and copying them.
                    tree_store.result = {
                        field: my_tree[selection, field] for field in afields
                    }

            else:
                tree_store.result_id = None

        # Use the global root to combine all results.
        # Both parts of this are fairly slow.
        if is_global_root and collect_results:
            my_trees = []
            pbar = get_pbar("Combining results", len(my_items))
            for i, my_item in enumerate(my_items):
                my_tree = trees[my_item]
                my_trees.append(my_tree)
                my_root = my_tree.find_root()
                key = (my_root._arbor_index, my_tree.tree_id)
                data = arbor_storage[key]

                if save_roots_only:
                    indices = my_tree.tree_id
                elif my_tree.is_root:
                    indices = slice(None)
                else:
                    indices = [my_tree._tree_field_indices]

                for field in afields:
                    if field not in my_root.field_data:
                        arbor._node_io._initialize_analysis_field(my_root, field)

                    my_root.field_data[field][indices] = data[field]
                pbar.update(i + 1)
            pbar.finish()

            if do_save:
                if save_in_place:
                    save_trees = my_trees
                else:
                    save_trees = trees

                fn = arbor.save_arbor(
                    filename=filename,
                    trees=save_trees,
                    save_in_place=save_in_place,
                    save_roots_only=save_roots_only,
                )

                new_arbor = ytree_load(fn)
                new_arbor._restore_derived_fields_from(arbor)
                arbor = new_arbor

                trees = [
                    regenerate_node(arbor, tree, new_index=i)
                    for i, tree in enumerate(trees)
                ]


def parallel_tree_nodes(tree, group="forest", nodes=None, njobs=0, dynamic=False):
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
    nodes: optional, list
        A list of nodes to iterate over instead of using a forest, tree, or
        prog selection. If provided, this will supersede the value of the
        "group" keyword. Note, all nodes must be members of the tree given
        in the "tree" argument.
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

    afields = tree.arbor.analysis_field_list

    if nodes is None:
        my_halos = list(tree[group])
    else:
        my_halos = nodes

    tree_storage = {}
    for halo_store, ihalo in parallel_objects(
        range(len(my_halos)), storage=tree_storage, njobs=njobs, dynamic=dynamic
    ):
        my_halo = my_halos[ihalo]
        yield my_halo
        if yt_is_root():
            halo_store.result_id = my_halo.tree_id
            halo_store.result = {field: my_halo[field] for field in afields}
        else:
            halo_store.result_id = -1

    # combine results for this tree
    if yt_is_root():
        for tree_id, result in sorted(tree_storage.items()):
            if tree_id == -1:
                continue
            my_halo = tree.get_node("forest", tree_id)

            for field, value in result.items():
                my_halo[field] = value


def parallel_nodes(
    trees,
    group="forest",
    collect_results=True,
    save_every=None,
    save_in_place=None,
    filename=None,
    njobs=None,
    dynamic=None,
):
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
    collect_results : optional, bool
        If True, then results stored in analysis fields will be collected
        by the root process. This must be set to True if saving is to be
        done. If False, results collection is ignored. This will result in
        a significant speedup. If you have no intention of altering analysis
        fields or do not need results to be recollected or saved, then this is
        the best option. Setting this to False will automatically set
        save_every to False as well.
        Default: True
    save_every : optional, int or False
        Number of trees to be completed before results are saved. This is used to
        save intermediate results in case scripts need to be restarted. This
        parameter results in different behavior depending on the value of the
        collect_results keyword. If save_every is set to:

            - integer: if collect_trees is True, the number of trees to complete
              before saving. If collect_trees is False, a ValueError exception will
              be raised.
            - False: no saving will be done. Results will still be collected if
              collect_results is True.
            - None: if collect_results if True, save will occur after iterating over
              all trees. If collect_results is False, no saving will be done.

        Default: None
    save_in_place : optional, bool or None
        If True, analysis fields will be saved to the original
        arbor, even if only a subset of all trees is provided
        with the trees keyword. This will essentially "update"
        the arbor in place. If False and only a subset of
        all trees is provided, a new arbor will be created
        containing only the trees provided. If set to None,
        behavior is determined by the type of arbor loaded.
        If the arbor is a YTreeArbor (i.e., saved with
        save_arbor), save_in_place will be set to True. If
        not of this type, it will be set to False.
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
        trees,
        collect_results=collect_results,
        save_every=save_every,
        save_in_place=save_in_place,
        filename=filename,
        njobs=njobs[0],
        dynamic=dynamic[0],
    ):
        for node in parallel_tree_nodes(
            tree, group=group, njobs=njobs[1], dynamic=dynamic[1]
        ):
            yield node
