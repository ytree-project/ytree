"""
parallel_trees test script



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

comm = MPI.Comm.Get_parent()

fn = sys.argv[1]
a = ytree.load(fn)
if "test_field" not in a.field_list:
    a.add_analysis_field("test_field", default=-1, units="Msun")

trees = list(a[:])

for tree in ytree.parallel_trees(trees, njobs=0, dynamic=False, save_every=8):
    for node in tree["forest"]:
        root = node.root
        yt.mylog.info(f"Doing {node.tree_id}/{root.tree_size} of {root._arbor_index}")
        node["test_field"] = 2 * node["mass"]

comm.Disconnect()
