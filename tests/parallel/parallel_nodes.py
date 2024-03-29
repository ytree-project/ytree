"""
parallel_nodes test script



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
from ytree.utilities.testing import get_tree_split
import ytree

def run():
    input_fn, output_fn, selection, group = sys.argv[1:5]
    njobs = tuple([int(arg) for arg in sys.argv[5:7]])
    dynamic = tuple([bool(int(arg)) for arg in sys.argv[7:9]])
    if len(sys.argv) > 9:
        save_every = int(sys.argv[9])
    else:
        save_every = None

    a = ytree.load(input_fn)
    if "test_field" not in a.field_list:
        a.add_analysis_field("test_field", default=-1, units="Msun")

    if selection == "all":
        trees = list(a[:8])
    elif selection == "nonroot":
        trees = get_tree_split(a)
    else:
        print (f"Bad selection: {selection}.")
        sys.exit(1)

    for node in ytree.parallel_nodes(trees, group=group,
                                     njobs=njobs, dynamic=dynamic,
                                     save_every=save_every, filename=output_fn):
        root = node.root
        yt.mylog.info(f"Doing {node.tree_id}/{root.tree_size} of {root._arbor_index}")
        node["test_field"] = 2 * node["mass"]


if __name__ == "__main__":
    comm = MPI.Comm.Get_parent()
    try:
        run()
    except BaseException:
        pass
    comm.Disconnect()
