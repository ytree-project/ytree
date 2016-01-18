import numpy as np
import yt

from yt.utilities.parallel_tools.parallel_analysis_interface import \
    _get_comm

from .ancestry_checker import \
    ancestry_checker_registry
from .halo_selector import \
    selector_registry

class SimpleTree(object):
    def __init__(self, time_series):
        self.ts = time_series

        # set a default selector
        self.set_selector("sphere", "Group_R_Crit200", factor=5)

        # set a default ancestry checker
        self.set_ancestry_checker("common_ids")

    def set_selector(self, selector, *args, **kwargs):
        self.selector = selector_registry.find(selector, *args, **kwargs)

    def set_ancestry_checker(self, ancestry_checker, *args, **kwargs):
        self.ancestry_checker = \
          ancestry_checker_registry.find(ancestry_checker, *args, **kwargs)

    def find_ancestors(self, halo_type, halo_id, ds1, ds2):
        comm = _get_comm(())
        if comm.rank == 0:
            hc = ds1.halo(halo_type, halo_id)
            halo_member_ids = hc["member_ids"]
            candidate_ids = self.selector(hc, ds2)
        else:
            candidate_ids = None
            halo_member_ids = None
        if comm.comm is not None:
            candidate_ids = comm.comm.bcast(candidate_ids, root=0)
            halo_member_ids = comm.comm.bcast(halo_member_ids, root=0)

        ancestors = []
        for candidate_id in yt.parallel_objects(candidate_ids, njobs=-1):
            candidate = ds2.halo(halo_type, candidate_id)
            candidate_member_ids = candidate["member_ids"]
            if self.ancestry_checker(halo_member_ids, candidate_member_ids):
                ancestors.append(candidate_id)
        return ancestors

    def trace_lineage(self, halo_type, halo_ids):
        outputs_r = self.ts.outputs[::-1]
        ds1 = yt.load(outputs_r[0])
        current_ids = halo_ids

        all_ancestor_ids = []
        all_ancestor_counts = []
        all_descendent_ids = []

        for fn in outputs_r[1:]:
            ds2 = yt.load(fn)

            if yt.is_root():
                yt.mylog.info("Searching for ancestors of %d halos." %
                              len(current_ids))

            these_ancestor_ids = []
            these_ancestor_counts = []
            these_descendent_ids = []

            comm = _get_comm(())
            njobs = min(comm.size, len(current_ids))
            for current_id in yt.parallel_objects(current_ids, njobs=njobs):
                ancestor_ids = self.find_ancestors(
                    halo_type, current_id, ds1, ds2)
                these_ancestor_ids.extend(ancestor_ids)
                these_ancestor_counts.append(len(ancestor_ids))
                these_descendent_ids.append(current_id)

            these_ancestor_ids = comm.par_combine_object(
                these_ancestor_ids, "cat", datatype="list")
            these_ancestor_counts = comm.par_combine_object(
                these_ancestor_counts, "cat", datatype="list")
            these_descendent_ids = comm.par_combine_object(
                these_descendent_ids, "cat", datatype="list")

            all_ancestor_ids.append(these_ancestor_ids)
            all_ancestor_counts.append(these_ancestor_counts)
            all_descendent_ids.append(these_descendent_ids)

            ds1 = ds2
            current_ids = these_ancestor_ids
            if len(current_ids) == 0:
                break

        return # need to return something
