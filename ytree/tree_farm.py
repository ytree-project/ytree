"""
TreeFarm class and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) 2016, Britton Smith <brittonsmith@gmail.com>
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import numpy as np
import os
import yt

from yt.funcs import \
    ensure_dir, \
    get_output_filename, \
    iterable
from yt.utilities.parallel_tools.parallel_analysis_interface import \
    _get_comm

from ytree.ancestry_checker import \
    ancestry_checker_registry
from ytree.ancestry_filter import \
    ancestry_filter_registry
from ytree.ancestry_short import \
    ancestry_short_registry
from ytree.halo_selector import \
    selector_registry, \
    clear_id_cache

class TreeFarm(object):
    def __init__(self, time_series, setup_function=None):
        self.ts = time_series
        self.setup_function = setup_function

        # set a default selector
        self.set_selector("all")

        # set a default ancestry checker
        self.set_ancestry_checker("common_ids")

        self.ancestry_filter = None
        self.ancestry_short = None
        self.comm = _get_comm(())

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

    def _load_ds(self, filename):
        ds = yt.load(filename)
        if self.setup_function is not None:
            self.setup_function(ds)
        return ds

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
                candidate.descendent_identifier = hc.particle_identifier
                ancestors.append(candidate)
                if self.ancestry_short is not None and \
                  self.ancestry_short(hc, candidate):
                    break

        id_store.extend([ancestor.particle_identifier
                         for ancestor in ancestors])

        if self.ancestry_filter is not None:
            ancestors = self.ancestry_filter(hc, ancestors)

        return ancestors

    def find_descendent(self, hc, ds2):
        halo_member_ids = hc["member_ids"].d.astype(np.int64)
        candidate_ids = self.selector(hc, ds2)

        for candidate_id in candidate_ids:
            candidate = ds2.halo(hc.ptype, candidate_id)
            candidate_member_ids = candidate["member_ids"].d.astype(np.int64)
            hc.descendent_identifier = -1
            if self.ancestry_checker(candidate_member_ids, halo_member_ids):
                hc.descendent_identifier = candidate.particle_identifier
                break

    def trace_ancestors(self, halo_type, root_ids,
                        halo_properties=None, filename=None):

        output_dir = os.path.dirname(filename)
        if yt.is_root() and len(output_dir) > 0:
            ensure_dir(output_dir)

        all_outputs = self.ts.outputs[::-1]
        ds1 = None

        for i, fn2 in enumerate(all_outputs[1:]):
            fn1 = all_outputs[i]
            target_filename = get_output_filename(
                filename, "%s.%d" % (os.path.basename(fn1), 0), ".h5")
            catalog_filename = get_output_filename(
                filename, "%s.%d" % (os.path.basename(fn2), 0), ".h5")
            if os.path.exists(catalog_filename):
                continue

            if ds1 is None:
                ds1 = self._load_ds(fn1)
            ds2 = self._load_ds(fn2)
            if ds2.index.particle_count[halo_type] == 0:
                yt.mylog.info("%s has no halos of type %s, ending." %
                              (ds2, halo_type))
                break

            if i == 0:
                target_ids = root_ids
                if not iterable(target_ids):
                    target_ids = np.array([target_ids])
                if isinstance(target_ids, yt.YTArray):
                    target_ids = target_ids.d
                if target_ids.dtype != np.int64:
                    target_ids = target_ids.astype(np.int64)
            else:
                yt.mylog.info("Loading target ids from %s.",
                              target_filename)
                ds_target = yt.load(target_filename)
                target_ids = \
                  ds_target.r["halos",
                              "particle_identifier"].d.astype(np.int64)
                del ds_target

            id_store = []
            target_halos = []
            ancestor_halos = []

            njobs = min(self.comm.size, target_ids.size)
            pbar = yt.get_pbar("Linking halos (%s - %s)" % (ds1, ds2),
                               target_ids.size, parallel=True)
            my_i = 0
            for halo_id in yt.parallel_objects(target_ids, njobs=njobs):
                my_halo = ds1.halo(halo_type, halo_id)

                target_halos.append(my_halo)
                my_ancestors = self.find_ancestors(my_halo, ds2,
                                                   id_store=id_store)
                ancestor_halos.extend(my_ancestors)
                my_i += njobs
                pbar.update(my_i)
            pbar.finish()

            if i == 0:
                for halo in target_halos:
                    halo.descendent_identifier = -1
                self._save_catalog(filename, ds1, target_halos,
                                   halo_properties)
            self._save_catalog(filename, ds2, ancestor_halos,
                               halo_properties)

            if len(ancestor_halos) == 0:
                break

            ds1 = ds2
            clear_id_cache()

    def trace_descendents(self, halo_type,
                          halo_properties=None, filename=None):

        output_dir = os.path.dirname(filename)
        if yt.is_root() and len(output_dir) > 0:
            ensure_dir(output_dir)

        all_outputs = self.ts.outputs[:]
        ds1 = ds2 = None

        for i, fn2 in enumerate(all_outputs[1:]):
            fn1 = all_outputs[i]
            target_filename = get_output_filename(
                filename, "%s.%d" % (os.path.basename(fn1), 0), ".h5")
            catalog_filename = get_output_filename(
                filename, "%s.%d" % (os.path.basename(fn2), 0), ".h5")
            if os.path.exists(target_filename):
                continue

            if ds1 is None:
                ds1 = self._load_ds(fn1)
            ds2 = self._load_ds(fn2)

            target_halos = []

            if ds1.index.particle_count[halo_type] == 0:
                yt.mylog.info("%s has no halos of type %s." %
                              (ds1, halo_type))
                self._save_catalog(filename, ds1, target_halos,
                                   halo_properties)
                ds1 = ds2
                continue

            target_ids = \
              ds1.r[halo_type, "particle_identifier"].d.astype(np.int64)

            njobs = min(self.comm.size, target_ids.size)
            pbar = yt.get_pbar("Linking halos (%s - %s)" % (ds1, ds2),
                               target_ids.size, parallel=True)
            my_i = 0
            for halo_id in yt.parallel_objects(target_ids, njobs=njobs):
                my_halo = ds1.halo(halo_type, halo_id)

                target_halos.append(my_halo)
                self.find_descendent(my_halo, ds2)
                my_i += njobs
                pbar.update(my_i)
            pbar.finish()

            self._save_catalog(filename, ds1, target_halos,
                               halo_properties)
            ds1 = ds2
            clear_id_cache()

        if os.path.exists(catalog_filename):
            return

        if ds2 is None:
            ds2 = self._load_ds(fn2)
        self._save_catalog(filename, ds2, halo_type,
                           halo_properties)

    def _save_catalog(self, filename, ds, halos, halo_properties=None):
        if self.comm is None:
            rank = 0
        else:
            rank = self.comm.rank
        filename = get_output_filename(
            filename, "%s.%d" % (str(ds.basename), rank), ".h5")

        if halo_properties is None:
            my_hp = []
        else:
            my_hp = halo_properties[:]

        fields = ["particle_identifier",
                  "descendent_identifier",
                  "particle_mass"] + \
                 ["particle_position_%s" % ax for ax in "xyz"] + \
                 ["particle_velocity_%s" % ax for ax in "xyz"]
        for field in fields:
            if field not in my_hp:
                my_hp.append(field)

        if isinstance(halos, list):
            num_halos = len(halos)
            data = self._create_halo_data_lists(halos, my_hp)
        else:
            num_halos = ds.index.particle_count[halos]
            data = dict((field, ds.r[halos, field].in_base())
                        for field in my_hp
                        if field != "descendent_identifier")
            data["descendent_identifier"] = -1 * np.ones(num_halos)
        ftypes = dict([(field, ".") for field in data])
        extra_attrs = {"num_halos": num_halos,
                       "data_type": "halo_catalog"}
        yt.save_as_dataset(ds, filename, data, field_types=ftypes,
                           extra_attrs=extra_attrs)

    def _create_halo_data_lists(self, halos, halo_properties):
        pbar = yt.get_pbar("Gathering field data from halos",
                           self.comm.size*len(halos), parallel=True)
        data = dict([(hp, []) for hp in halo_properties])
        my_i = 0
        for halo in halos:
            for hp in halo_properties:
                data[hp].append(_get_halo_property(halo, hp))
            my_i += self.comm.size
            pbar.update(my_i)
        pbar.finish()
        for hp in halo_properties:
            if data[hp] and hasattr(data[hp][0], "units"):
                data[hp] = yt.YTArray(data[hp]).in_base()
            else:
                data[hp] = np.array(data[hp])
            shape = data[hp].shape
            if len(shape) > 1 and shape[-1] == 1:
                data[hp] = np.reshape(data[hp], shape[:-1])
        return data

def _get_halo_property(halo, halo_property):
    val = getattr(halo, halo_property, None)
    if val is None: val = halo[halo_property]
    return val
