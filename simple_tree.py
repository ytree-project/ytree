import numpy as np
import yt

from yt.utilities.parallel_tools.parallel_analysis_interface import \
    _get_comm

from .ancestry_checker import \
    ancestry_checker_registry
from .ancestry_filter import \
    ancestry_filter_registry
from .communication import \
    mpi_gather_list
from .halo_selector import \
    selector_registry

class SimpleTree(object):
    def __init__(self, time_series):
        self.ts = time_series

        # set a default selector
        self.set_selector("sphere", "Group_R_Crit200", factor=5)

        # set a default ancestry checker
        self.set_ancestry_checker("common_ids")

        self.ancestry_filter = None

    def set_selector(self, selector, *args, **kwargs):
        self.selector = selector_registry.find(selector, *args, **kwargs)

    def set_ancestry_checker(self, ancestry_checker, *args, **kwargs):
        self.ancestry_checker = \
          ancestry_checker_registry.find(ancestry_checker, *args, **kwargs)

    def set_ancestry_filter(self, ancestry_filter, *args, **kwargs):
        self.ancestry_filter = \
          ancestry_filter_registry.find(ancestry_filter, *args, **kwargs)

    def find_ancestors(self, halo_type, halo_id, ds1, ds2):
        hc = ds1.halo(halo_type, halo_id)
        halo_member_ids = hc["member_ids"].d.astype(np.int64)
        candidate_ids = self.selector(hc, ds2)

        ancestors = []
        for candidate_id in candidate_ids:
            candidate = ds2.halo(halo_type, candidate_id)
            candidate_member_ids = candidate["member_ids"].d.astype(np.int64)
            if self.ancestry_checker(halo_member_ids, candidate_member_ids):
                ancestors.append(candidate)

        if self.ancestry_filter is not None:
            ancestors = self.ancestry_filter(hc, ancestors)

        return hc, ancestors

    def trace_lineage(self, halo_type, root_ids, halo_properties=None):
        if halo_properties is None:
            halo_properties = []

        comm = _get_comm(())
        outputs_r = self.ts.outputs[::-1]
        ds1 = yt.load(outputs_r[0])

        all_halo_ids = [root_ids]
        all_ancestor_counts = []

        all_halo_properties = dict([(halo_property, [[]])
                                    for halo_property in halo_properties])
        for current_id in yt.parallel_objects(all_halo_ids[-1], njobs=-1):
            hc = ds1.halo(halo_type, current_id)
            for halo_property in halo_properties:
                all_halo_properties[halo_property][0].append(
                    get_halo_property(hc, halo_property))
        if comm.comm is not None:
            for halo_property in halo_properties:
                all_halo_properties[halo_property][0] = \
                  mpi_gather_list(comm.comm, all_halo_properties[halo_property][0])

        for fn in outputs_r[1:]:
            ds2 = yt.load(fn)

            if yt.is_root():
                yt.mylog.info("Searching for ancestors of %d halos." %
                              len(all_halo_ids[-1]))

            these_ancestor_ids = []
            these_ancestor_counts = []
            these_halo_properties = \
              dict([(halo_property, []) for halo_property in halo_properties])

            njobs = min(comm.size, len(all_halo_ids[-1]))
            for current_id in yt.parallel_objects(all_halo_ids[-1], njobs=-1):
                current_halo, ancestors = self.find_ancestors(
                    halo_type, current_id, ds1, ds2)

                for halo_property in halo_properties:
                    these_halo_properties[halo_property].extend(
                        [get_halo_property(ancestor, halo_property)
                         for ancestor in ancestors])

                these_ancestor_ids.extend([ancestor.particle_identifier
                                           for ancestor in ancestors])
                these_ancestor_counts.append(len(ancestors))

            these_ancestor_ids = comm.par_combine_object(
                these_ancestor_ids, "cat", datatype="list")
            these_ancestor_counts = comm.par_combine_object(
                these_ancestor_counts, "cat", datatype="list")
            if comm.comm is not None:
                for halo_property in these_halo_properties:
                    these_halo_properties[halo_property] = \
                      mpi_gather_list(comm.comm, these_halo_properties[halo_property])

            all_ancestor_counts.append(these_ancestor_counts)
            for halo_property in these_halo_properties:
                all_halo_properties[halo_property].append(
                    these_halo_properties[halo_property])
            if len(these_ancestor_ids) > 0:
                all_halo_ids.append(these_ancestor_ids)
            else:
                break
            ds1 = ds2

        return # need to return something

def get_halo_property(halo, halo_property):
    val = getattr(halo, halo_property, None)
    if val is None: val = halo[halo_property]
    return val
