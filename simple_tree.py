import numpy as np
import os
import yt

from yt.funcs import \
    ensure_dir, \
    get_output_filename
from yt.utilities.parallel_tools.parallel_analysis_interface import \
    _get_comm, \
    parallel_root_only

from .ancestry_checker import \
    ancestry_checker_registry
from .ancestry_filter import \
    ancestry_filter_registry
from .ancestry_short import \
    ancestry_short_registry
from .communication import \
    mpi_gather_list
from .halo_selector import \
    selector_registry, \
    clear_id_cache

class SimpleTree(object):
    def __init__(self, time_series, setup_function=None):
        self.ts = time_series
        self.setup_function = setup_function

        # set a default selector
        self.set_selector("sphere", "Group_R_Crit200", factor=5)

        # set a default ancestry checker
        self.set_ancestry_checker("common_ids")

        self.ancestry_filter = None
        self.ancestry_short = None

    def set_selector(self, selector, *args, **kwargs):
        self.selector = selector_registry.find(selector, *args, **kwargs)

    def set_ancestry_checker(self, ancestry_checker, *args, **kwargs):
        self.ancestry_checker = \
          ancestry_checker_registry.find(ancestry_checker, *args, **kwargs)

    def set_ancestry_filter(self, ancestry_filter, *args, **kwargs):
        self.ancestry_filter = \
          ancestry_filter_registry.find(ancestry_filter, *args, **kwargs)

    def set_ancestry_short(self, ancestry_short, *args, **kwargs):
        self.ancestry_short = \
          ancestry_short_registry.find(ancestry_short, *args, **kwargs)

    def find_ancestors(self, hc, ds2, id_store=None):
        if id_store is None: id_store = []
        halo_member_ids = hc["member_ids"].d.astype(np.int64)
        candidate_ids = self.selector(hc, ds2)

        ancestors = []
        for candidate_id in candidate_ids:
            if candidate_id in id_store: continue
            candidate = ds2.halo(hc.ptype, candidate_id)
            candidate_member_ids = candidate["member_ids"].d.astype(np.int64)
            if self.ancestry_checker(halo_member_ids, candidate_member_ids):
                ancestors.append(candidate)
                if self.ancestry_short is not None and \
                        self.ancestry_short(hc, candidate):
                    break

        id_store.extend([ancestor.particle_identifier
                         for ancestor in ancestors])

        if self.ancestry_filter is not None:
            ancestors = self.ancestry_filter(hc, ancestors)

        return ancestors

    def _load_halo_objects(self, ds, filename):
        pass

    def load_ds(self, filename):
        ds = yt.load(filename)
        if self.setup_function is not None:
            self.setup_function(ds)
        return ds

    def trace_lineage_2(self, halo_type, root_ids,
                        halo_properties=None, filename=None):

        filename = get_output_filename(filename, "tree", ".h5")
        output_dir = os.path.dirname(filename)
        if yt.is_root(): ensure_dir(output_dir)

        comm = _get_comm(())
        all_outputs = self.ts.outputs[::-1]
        ds1 = None

        for i, fn in enumerate(all_outputs[1:]):
            segment_file = os.path.join(output_dir, "tree_segment_%04d.h5")
            if os.path.exists(segment_file): continue

            if ds1 is None:
                ds1 = self.load_ds(all_outputs[i])
            ds2 = self.load_ds(fn)

            if i == 0:
                target_ids = root_ids
            else:
                raise RuntimeError("not there yet!")

            id_store = []
            all_links = []
            target_halos = []
            ancestor_halos = []

            njobs = min(comm.size, len(target_ids))
            pbar = yt.get_pbar("Linking halos:", len(target_ids))
            for i_halo, halo_id in yt.parallel_objects(enumerate(target_ids), njobs=njobs):
                my_halo = ds1.halo(halo_type, halo_id)

                target_halos.append(my_halo)
                my_ancestors = self.find_ancestors(my_halo, ds2, id_store=id_store)
                all_links.extend([[my_halo.particle_identifier, my_ancestor.particle_identifier]
                                  for my_ancestor in my_ancestors])
                ancestor_halos.extend(my_ancestors)
                pbar.update(i_halo)
            pbar.finish()

            import pdb ; pdb.set_trace()

            ds1 = ds2

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
        pbar = yt.get_pbar("Getting initial halos", len(all_halo_ids[-1]),
                           parallel=True)
        my_i = 0
        for current_id in yt.parallel_objects(all_halo_ids[-1], njobs=-1):
            hc = ds1.halo(halo_type, current_id)
            for hp in halo_properties:
                all_halo_properties[hp][0].append(
                    get_halo_property(hc, hp))
            my_i += comm.size
            pbar.update(my_i)
        pbar.finish()
        if comm.comm is not None:
            for hp in halo_properties:
                all_halo_properties[hp][0] = \
                  mpi_gather_list(comm.comm, all_halo_properties[hp][0])

        for fn in outputs_r[1:]:
            id_store = []
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
            pbar = yt.get_pbar("Getting ancestors", len(all_halo_ids[-1]), parallel=True)
            my_i = 0
            for current_id in yt.parallel_objects(all_halo_ids[-1], njobs=-1):
                current_halo, ancestors = self.find_ancestors(
                    halo_type, current_id, ds1, ds2, id_store=id_store)

                for hp in halo_properties:
                    these_halo_properties[hp].extend(
                        [get_halo_property(ancestor, hp) for ancestor in ancestors])

                these_ancestor_ids.extend([ancestor.particle_identifier
                                           for ancestor in ancestors])
                these_ancestor_counts.append(len(ancestors))
                my_i += comm.size
                pbar.update(my_i)
            pbar.finish()

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
            clear_id_cache()

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
