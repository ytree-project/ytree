"""
parallel_tree_nodes test script



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

from mpi4py import MPI
import sys
import yt
yt.enable_parallelism()
import ytree

def run():
    fn = sys.argv[1]
    group = sys.argv[2]
    njobs = int(sys.argv[3])
    dynamic = bool(int(sys.argv[4]))

    a = ytree.load(fn)
    if "test_field" not in a.field_list:
        a.add_analysis_field("test_field", default=-1, units="Msun")

    trees = list(a[:])

    for tree in trees:
        for node in ytree.parallel_tree_nodes(tree, group=group,
                                              njobs=njobs, dynamic=dynamic):
            root = node.root
            yt.mylog.info(f"Doing {node.tree_id}/{root.tree_size} of {root._arbor_index}")
            node["test_field"] = 2 * node["mass"]

    if yt.is_root():
        a.save_arbor(trees=trees)


if __name__ == "__main__":
    comm = MPI.Comm.Get_parent()
    try:
        run()
    except BaseException:
        pass
    comm.Disconnect()
