import numpy as np
import yt

from yt.funcs import \
    get_output_filename
from yt.utilities.parallel_tools.parallel_analysis_interface import \
    _get_comm, \
    parallel_root_only

from .ancestry_checker import \
    ancestry_checker_registry
from .ancestry_filter import \
    ancestry_filter_registry
from .communication import \
    mpi_gather_list
from .halo_selector import \
    selector_registry

class SimpleTree(object):
    def __init__(self, time_series, setup_function=None):
        self.ts = time_series
        self.setup_function = setup_function

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

    def trace_lineage(self, halo_type, root_ids,
                      halo_properties=None, filename=None):
        if halo_properties is None:
            halo_properties = []

        comm = _get_comm(())
        outputs_r = self.ts.outputs[::-1]
        ds1 = yt.load(outputs_r[0])
        if self.setup_function is not None:
            self.setup_function(ds1)
        ds_props = dict([(attr, getattr(ds1, attr))
                         for attr in ["domain_left_edge", "domain_right_edge",
                                      "omega_matter", "omega_lambda",
                                      "hubble_constant"]])

        all_redshift = [ds1.current_redshift]
        all_halo_ids = [root_ids]
        all_ancestor_counts = [[len(root_ids)]]

        all_halo_properties = dict([(hp, [[]]) for hp in halo_properties])
        for current_id in yt.parallel_objects(all_halo_ids[-1], njobs=-1):
            hc = ds1.halo(halo_type, current_id)
            for hp in halo_properties:
                all_halo_properties[hp][0].append(
                    get_halo_property(hc, hp))
        if comm.comm is not None:
            for hp in halo_properties:
                all_halo_properties[hp][0] = \
                  mpi_gather_list(comm.comm, all_halo_properties[hp][0])

        for fn in outputs_r[1:]:
            ds2 = yt.load(fn)
            if self.setup_function is not None:
                self.setup_function(ds2)

            if yt.is_root():
                yt.mylog.info("Searching for ancestors of %d halos." %
                              len(all_halo_ids[-1]))

            these_ancestor_ids = []
            these_ancestor_counts = []
            these_halo_properties = dict([(hp, []) for hp in halo_properties])

            njobs = min(comm.size, len(all_halo_ids[-1]))
            for current_id in yt.parallel_objects(all_halo_ids[-1], njobs=-1):
                current_halo, ancestors = self.find_ancestors(
                    halo_type, current_id, ds1, ds2)

                for hp in halo_properties:
                    these_halo_properties[hp].extend(
                        [get_halo_property(ancestor, hp) for ancestor in ancestors])

                these_ancestor_ids.extend([ancestor.particle_identifier
                                           for ancestor in ancestors])
                these_ancestor_counts.append(len(ancestors))

            these_ancestor_ids = comm.par_combine_object(
                these_ancestor_ids, "cat", datatype="list")
            these_ancestor_counts = comm.par_combine_object(
                these_ancestor_counts, "cat", datatype="list")
            if comm.comm is not None:
                for hp in halo_properties:
                    these_halo_properties[hp] = \
                      mpi_gather_list(comm.comm, these_halo_properties[hp])

            if len(these_ancestor_ids) == 0: break

            all_halo_ids.append(these_ancestor_ids)
            all_ancestor_counts.append(these_ancestor_counts)
            for hp in halo_properties:
                all_halo_properties[hp].append(these_halo_properties[hp])
            all_redshift.append(ds2.current_redshift)
            ds1 = ds2

        return self.save_tree(filename, ds_props, all_redshift,
                              all_halo_ids, all_ancestor_counts,
                              all_halo_properties)

    @parallel_root_only
    def save_tree(self, filename, ds_properties, redshift,
                  halo_ids, ancestor_counts, halo_properties):
        filename = get_output_filename(filename, "tree", ".h5")
        redshift = np.array(redshift)
        halo_ids_flat = []
        ancestor_counts_flat = []
        halo_properties_flat = dict([(hp, []) for hp in halo_properties])
        for i in range(redshift.size):
            halo_ids_flat.extend(halo_ids[i])
            ancestor_counts_flat.extend(ancestor_counts[i])
            for hp in halo_properties:
                halo_properties_flat[hp].extend(halo_properties[hp][i])
        data = {"redshift": redshift}
        data["halo_ids"] = np.array(halo_ids_flat).astype(np.float64)
        data["ancestor_counts"] = np.array(ancestor_counts_flat).astype(np.float64)
        for hp in halo_properties:
            data[hp] = yt.YTArray(halo_properties_flat[hp])

        return yt.save_as_dataset(ds_properties, filename, data)

def get_halo_property(halo, halo_property):
    val = getattr(halo, halo_property, None)
    if val is None: val = halo[halo_property]
    return val.in_cgs()
