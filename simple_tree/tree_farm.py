import h5py
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

class TreeFarm(object):
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

    def _load_ancestor_ids(self, filename):
        fh = h5py.File(filename, "r")
        halo_ids = fh["/data/ancestor_particle_identifier"].value
        fh.close()
        return halo_ids

    def _load_ds(self, filename):
        ds = yt.load(filename)
        if self.setup_function is not None:
            self.setup_function(ds)
        return ds

    def save_segment(self, filename, ds1, ds2, descendent_halos, ancestor_halos,
                     halo_links, halo_properties=None):
        if halo_properties is None:
            my_hp = []
        else:
            my_hp = halo_properties[:]
        if "particle_identifier" not in my_hp:
            my_hp.append("particle_identifier")

        descendent_data = create_halo_data_lists(ds1, descendent_halos, my_hp)
        ancestor_data = create_halo_data_lists(ds1, ancestor_halos, my_hp)

        data = {"links": halo_links}
        for field in descendent_data:
            data["descendent_%s" % field] = descendent_data[field]
        for field in ancestor_data:
            data["ancestor_%s" % field] = ancestor_data[field]
        del descendent_data, ancestor_data

        comm = _get_comm(())
        if comm.comm is not None:
            for field in data:
                data[field] = mpi_gather_list(comm.comm, data[field])

        if yt.is_root():
            for field in data:
                if field in ["links", "descendent_particle_identifier",
                             "ancestor_particle_identifier"]:
                    data[field] = np.array(data[field], dtype=np.int64)
                elif "descendent" in field:
                    data[field] = ds1.arr(data[field])
                elif "ancestor" in field:
                    data[field] = ds2.arr(data[field])
                else:
                    raise RuntimeError("Bad field: %s." % field)

            my_ds = dict([(attr, getattr(ds1, attr))
                          for attr in ["dimensionality",
                                       "domain_left_edge", "domain_right_edge",
                                       "domain_dimensions", "periodicity",
                                       "omega_lambda", "omega_matter",
                                       "hubble_constant"]])
            extra_attrs = \
                dict([("descendent_%s" % attr, getattr(ds1, attr))
                      for attr in ["current_time", "current_redshift"]])
            extra_attrs.update(
                dict([("ancestor_%s" % attr, getattr(ds2, attr))
                      for attr in ["current_time", "current_redshift"]]))
            return yt.save_as_dataset(my_ds, filename, data, extra_attrs=extra_attrs)

    def trace_ancestors(self, halo_type, root_ids,
                        halo_properties=None, filename=None):

        filename = get_output_filename(filename, "tree", ".h5")
        output_dir = os.path.dirname(filename)
        if yt.is_root() and len(output_dir) > 0: ensure_dir(output_dir)

        comm = _get_comm(())
        all_outputs = self.ts.outputs[::-1]
        ds1 = None

        for i, fn in enumerate(all_outputs[1:]):
            segment_file = os.path.join(output_dir, "tree_segment_%04d.h5" % i)
            if os.path.exists(segment_file): continue

            if ds1 is None:
                ds1 = self._load_ds(all_outputs[i])
            ds2 = self._load_ds(fn)

            if i == 0:
                target_ids = root_ids
            else:
                last_segment_file = os.path.join(output_dir,
                                                 "tree_segment_%04d.h5" % (i-1))
                target_ids = self._load_ancestor_ids(last_segment_file)

            id_store = []
            all_links = []
            target_halos = []
            ancestor_halos = []

            njobs = min(comm.size, len(target_ids))
            pbar = yt.get_pbar("Linking halos", len(target_ids), parallel=True)
            my_i = 0
            for halo_id in yt.parallel_objects(target_ids, njobs=njobs):
                my_halo = ds1.halo(halo_type, halo_id)

                target_halos.append(my_halo)
                my_ancestors = self.find_ancestors(my_halo, ds2, id_store=id_store)
                all_links.extend([[my_halo.particle_identifier,
                                   my_ancestor.particle_identifier]
                                  for my_ancestor in my_ancestors])
                ancestor_halos.extend(my_ancestors)
                my_i += njobs
                pbar.update(my_i)
            pbar.finish()

            self.save_segment(segment_file, ds1, ds2, target_halos, ancestor_halos,
                              all_links, halo_properties)

            if len(ancestor_halos) == 0:
                break

            ds1 = ds2
            clear_id_cache()

    def trace_descendents(self, halo_type,
                          halo_properties=None, filename=None):

        filename = get_output_filename(filename, "tree", ".h5")
        output_dir = os.path.dirname(filename)
        if yt.is_root() and len(output_dir) > 0: ensure_dir(output_dir)

        comm = _get_comm(())
        all_outputs = self.ts.outputs[:]
        ds2 = None

        for i, fn in enumerate(all_outputs[1:]):
            segment_file = os.path.join(output_dir, "tree_segment_%04d.h5" % i)
            if os.path.exists(segment_file): continue

            if ds2 is None:
                ds2 = self._load_ds(all_outputs[i])
            ds1 = self._load_ds(fn)

            id_store = []
            all_links = []
            target_halos = []
            ancestor_halos = []

            if ds1.index.particle_count[halo_type] > 0:

                ad = ds1.all_data()
                target_ids = ad[halo_type, "particle_identifier"].d.astype(np.int64)
                del ad

                njobs = min(comm.size, len(target_ids))
                pbar = yt.get_pbar("Linking halos", len(target_ids), parallel=True)
                my_i = 0
                for halo_id in yt.parallel_objects(target_ids, njobs=njobs):
                    my_halo = ds1.halo(halo_type, halo_id)

                    target_halos.append(my_halo)
                    my_ancestors = self.find_ancestors(my_halo, ds2, id_store=id_store)
                    all_links.extend([[my_halo.particle_identifier,
                                       my_ancestor.particle_identifier]
                                      for my_ancestor in my_ancestors])
                    ancestor_halos.extend(my_ancestors)
                    my_i += njobs
                    pbar.update(my_i)
                pbar.finish()

            self.save_segment(segment_file, ds1, ds2, target_halos, ancestor_halos,
                              all_links, halo_properties)

            ds2 = ds1
            clear_id_cache()

def create_halo_data_lists(ds, halos, halo_properties):
    data = dict([(hp, []) for hp in halo_properties])
    for halo in halos:
        for hp in halo_properties:
            data[hp].append(get_halo_property(halo, hp))
    return data

def get_halo_property(halo, halo_property):
    val = getattr(halo, halo_property, None)
    if val is None: val = halo[halo_property]
    if hasattr(val, "units"):
        return val.in_cgs()
    return val
