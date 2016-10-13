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

from yt.convenience import \
    load as yt_load
from yt.frontends.ytdata.utilities import \
    save_as_dataset
from yt.funcs import \
    ensure_dir, \
    get_pbar, \
    get_output_filename, \
    iterable
from yt.units.yt_array import \
    YTArray
from yt.utilities.parallel_tools.parallel_analysis_interface import \
    _get_comm, \
    parallel_objects

from ytree.ancestry_checker import \
    ancestry_checker_registry
from ytree.ancestry_filter import \
    ancestry_filter_registry
from ytree.ancestry_short import \
    ancestry_short_registry
from ytree.halo_selector import \
    selector_registry, \
    clear_id_cache
from ytree.utilities.logger import \
    set_parallel_logger, \
    ytreeLogger as mylog

class TreeFarm(object):
    r"""
    TreeFarm is the merger-tree creator for Gadget FoF and Subfind
    halo catalogs.

    TreeFarm can be used to create a merger-tree for the full set of
    halos, starting from the first catalog, or can be used to trace the
    ancestry of specific halos, starting from the last catalog.  The
    merger-tree process will create a new set of halo catalogs,
    containing necessary fields (positions, velocities, masses),
    user-requested fields, and descendent IDs for each halo.  These
    halo catalogs can be loaded at yt datasets.

    Parameters
    ----------
    time_series : yt DatasetSeries object
        A yt time-series object containing the datasets over which
        the merger-tree will be calculated.
    setup_function : optional, callable
        A function that accepts a yt Dataset object and performs any
        setup, such as adding derived fields.

    Examples
    --------

    To create a full merger tree:

    >>> import nummpy as np
    >>> import yt
    >>> import ytree
    >>> ts = yt.DatasetSeries("data/groups_*/fof_subhalo_tab*.0.hdf5")
    >>> my_tree = ytree.TreeFarm(ts)
    >>> my_tree.trace_descendents("Group", filename="all_halos/")
    >>> a = ytree.load("all_halos/fof_subhalo_tab_000.0.hdf5.0.h5")
    >>> m = a.arr([t["particle_mass"] for t in a.trees])
    >>> i = np.argmax(m)
    >>> print (a.trees[i].line("particle_mass").to("Msun/h"))

    To create a merger tree for a specific halo or set of halos:

    >>> import nummpy as np
    >>> import yt
    >>> import ytree
    >>> ts = yt.DatasetSeries("data/groups_*/fof_subhalo_tab*.0.hdf5")
    >>> ds = yt[-1]
    >>> i = np.argmax(ds.r["Group", "particle_mass"].d)
    >>> my_ids = ds.r["Group", "particle_identifier"][i_max]
    >>> my_tree = ytree.TreeFarm(ts)
    >>> my_tree.set_ancestry_filter("most_massive")
    >>> my_tree.set_ancestry_short("above_mass_fraction", 0.5)
    >>> my_tree.trace_ancestors("Group", my_ids, filename="my_halos/")
    >>> a = ytree.load("my_halos/fof_subhalo_tab_025.0.hdf5.0.h5")
    >>> print (a.trees[0].line("particle_mass").to("Msun/h"))

    """
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
        set_parallel_logger(self.comm)

    def set_selector(self, selector, *args, **kwargs):
        r"""
        Set the method for selecting candidate halos for tracing
        halo ancestry.

        The default selector is "all", i.e., check every halo for a
        possible match.  This can be slow.  The "sphere" selector
        can be used to specify that only halos within some sphere
        be checked.

        Parameters
        ----------
        selector : string
            Name of selector.
        """
        self.selector = selector_registry.find(selector, *args, **kwargs)

    def set_ancestry_checker(self, ancestry_checker, *args, **kwargs):
        r"""
        Set the method for determing if a halo is the ancestor of
        another halo.

        The default method defines an ancestor as a halo where at least
        50% of its particles are found in the descendent.

        Parameters
        ----------
        ancestry_checker : string
            Name of checking method.
        """
        self.ancestry_checker = \
          ancestry_checker_registry.find(ancestry_checker, *args, **kwargs)

    def set_ancestry_filter(self, ancestry_filter, *args, **kwargs):
        r"""
        Select a method for determining which ancestors are kept.
        The kept ancestors will have their ancestries tracked.  This
        can be used to speed up merger-trees for targeted halos by
        specifying that only the most massive ancestor be kept.

        Parameters
        ----------
        ancestry_filter : string
            Name of filter method.
        """
        self.ancestry_filter = \
          ancestry_filter_registry.find(ancestry_filter, *args, **kwargs)

    def set_ancestry_short(self, ancestry_short, *args, **kwargs):
        r"""
        Select a method for cutting short the ancestry search.

        This can be used to speed up merger-trees for targeted halos by
        specifying that the search come to an end when an ancestor with
        greater than 50% of the halo's mass has been found, thereby
        ensuring that the most massive halo has already been found.

        Parameters
        ----------
        ancestry_short : string
            Name of short-out method.
        """
        self.ancestry_short = \
          ancestry_short_registry.find(ancestry_short, *args, **kwargs)

    def _load_ds(self, filename, **kwargs):
        """
        Load a catalog as a yt dataset and call setup function.
        """
        ds = yt_load(filename, **kwargs)
        if self.setup_function is not None:
            self.setup_function(ds)
        return ds

    def _find_ancestors(self, hc, ds2, id_store=None):
        """
        Search for ancestors of a given halo.
        """
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

    def _find_descendent(self, hc, ds2):
        """
        Search for descendents of a given halo.
        """
        halo_member_ids = hc["member_ids"].d.astype(np.int64)
        candidate_ids = self.selector(hc, ds2)

        hc.descendent_identifier = -1
        for candidate_id in candidate_ids:
            candidate = ds2.halo(hc.ptype, candidate_id)
            candidate_member_ids = candidate["member_ids"].d.astype(np.int64)
            if self.ancestry_checker(candidate_member_ids, halo_member_ids):
                hc.descendent_identifier = candidate.particle_identifier
                break

    def trace_ancestors(self, halo_type, root_ids,
                        fields=None, filename=None):
        """
        Trace the ancestry of a given set of halos.

        A merger-tree for a specific set of halos will be created,
        starting with the last halo catalog and moving backward.

        Parameters
        ----------
        halo_type : string
            The type of halo, typically "FOF" for FoF groups or
            "Subfind" for subhalos.
        root_ids : integer or array of integers
            The halo IDs from the last halo catalog for the
            targeted halos.
        fields : optional, list of strings
            List of additional fields to be saved to halo catalogs.
        filename : optional, string
            Directory in which merger-tree catalogs will be saved.
        """

        output_dir = os.path.dirname(filename)
        if self.comm.rank == 0 and len(output_dir) > 0:
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
                ds1 = self._load_ds(fn1, index_ptype=halo_type)
            ds2 = self._load_ds(fn2, index_ptype=halo_type)

            if self.comm.rank == 0:
                _print_link_info(ds1, ds2)

            if ds2.index.particle_count[halo_type] == 0:
                mylog.info("%s has no halos of type %s, ending." %
                           (ds2, halo_type))
                break

            if i == 0:
                target_ids = root_ids
                if not iterable(target_ids):
                    target_ids = np.array([target_ids])
                if isinstance(target_ids, YTArray):
                    target_ids = target_ids.d
                if target_ids.dtype != np.int64:
                    target_ids = target_ids.astype(np.int64)
            else:
                mylog.info("Loading target ids from %s.", target_filename)
                ds_target = yt_load(target_filename)
                target_ids = \
                  ds_target.r["halos",
                              "particle_identifier"].d.astype(np.int64)
                del ds_target

            id_store = []
            target_halos = []
            ancestor_halos = []

            njobs = min(self.comm.size, target_ids.size)
            pbar = get_pbar("Linking halos",
                            target_ids.size, parallel=True)
            my_i = 0
            for halo_id in parallel_objects(target_ids, njobs=njobs):
                my_halo = ds1.halo(halo_type, halo_id)

                target_halos.append(my_halo)
                my_ancestors = self._find_ancestors(my_halo, ds2,
                                                    id_store=id_store)
                ancestor_halos.extend(my_ancestors)
                my_i += njobs
                pbar.update(my_i)
            pbar.finish()

            if i == 0:
                for halo in target_halos:
                    halo.descendent_identifier = -1
                self._save_catalog(filename, ds1, target_halos, fields)
            self._save_catalog(filename, ds2, ancestor_halos, fields)

            if len(ancestor_halos) == 0:
                break

            ds1 = ds2
            clear_id_cache()

    def trace_descendents(self, halo_type,
                          fields=None, filename=None):
        """
        Trace the descendents of all halos.

        A merger-tree for all halos will be created, starting
        with the first halo catalog and moving forward.

        Parameters
        ----------
        halo_type : string
            The type of halo, typically "FOF" for FoF groups or
            "Subfind" for subhalos.
        fields : optional, list of strings
            List of additional fields to be saved to halo catalogs.
        filename : optional, string
            Directory in which merger-tree catalogs will be saved.
        """

        output_dir = os.path.dirname(filename)
        if self.comm.rank == 0 and len(output_dir) > 0:
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
                ds1 = self._load_ds(fn1, index_ptype=halo_type)
            ds2 = self._load_ds(fn2, index_ptype=halo_type)

            if self.comm.rank == 0:
                _print_link_info(ds1, ds2)

            target_halos = []
            if ds1.index.particle_count[halo_type] == 0:
                self._save_catalog(filename, ds1, target_halos, fields)
                ds1 = ds2
                continue

            target_ids = \
              ds1.r[halo_type, "particle_identifier"].d.astype(np.int64)

            njobs = min(self.comm.size, target_ids.size)
            pbar = get_pbar("Linking halos",
                            target_ids.size, parallel=True)
            my_i = 0
            for halo_id in parallel_objects(target_ids, njobs=njobs):
                my_halo = ds1.halo(halo_type, halo_id)

                target_halos.append(my_halo)
                self._find_descendent(my_halo, ds2)
                my_i += njobs
                pbar.update(my_i)
            pbar.finish()

            self._save_catalog(filename, ds1, target_halos, fields)
            ds1 = ds2
            clear_id_cache()

        if os.path.exists(catalog_filename):
            return

        if ds2 is None:
            ds2 = self._load_ds(fn2, index_ptype=halo_type)
        if self.comm.rank == 0:
            self._save_catalog(filename, ds2, halo_type, fields)

    def _save_catalog(self, filename, ds, halos, fields=None):
        """
        Save halo catalog with descendent information.
        """
        if self.comm is None:
            rank = 0
        else:
            rank = self.comm.rank
        filename = get_output_filename(
            filename, "%s.%d" % (str(ds.basename), rank), ".h5")

        if fields is None:
            my_fields = []
        else:
            my_fields = fields[:]

        default_fields = \
          ["particle_identifier",
           "descendent_identifier",
           "particle_mass"] + \
           ["particle_position_%s" % ax for ax in "xyz"] + \
           ["particle_velocity_%s" % ax for ax in "xyz"]
        for field in default_fields:
            if field not in my_fields:
                my_fields.append(field)

        if isinstance(halos, list):
            num_halos = len(halos)
            data = self._create_halo_data_lists(halos, my_fields)
        else:
            num_halos = ds.index.particle_count[halos]
            data = dict((field, ds.r[halos, field].in_base())
                        for field in my_fields
                        if field != "descendent_identifier")
            data["descendent_identifier"] = -1 * np.ones(num_halos)
        ftypes = dict([(field, ".") for field in data])
        extra_attrs = {"num_halos": num_halos,
                       "data_type": "halo_catalog"}
        mylog.info("Saving catalog with %d halos to %s." %
                   (num_halos, filename))
        save_as_dataset(ds, filename, data, field_types=ftypes,
                        extra_attrs=extra_attrs)

    def _create_halo_data_lists(self, halos, fields):
        """
        Given a list of halo containers, return a dictionary
        of field values for all halos.
        """
        data = dict([(hp, []) for hp in fields])
        if len(halos) > 0:
            pbar = get_pbar("Gathering field data from halos",
                            self.comm.size*len(halos), parallel=True)
            my_i = 0
            for halo in halos:
                for hp in fields:
                    data[hp].append(_get_halo_property(halo, hp))
                my_i += self.comm.size
                pbar.update(my_i)
            pbar.finish()
        for hp in fields:
            if data[hp] and hasattr(data[hp][0], "units"):
                data[hp] = YTArray(data[hp]).in_base()
            else:
                data[hp] = np.array(data[hp])
            shape = data[hp].shape
            if len(shape) > 1 and shape[-1] == 1:
                data[hp] = np.reshape(data[hp], shape[:-1])
        return data

def _get_halo_property(halo, halo_property):
    """
    Convenience function for querying fields and
    other properties from halo containers.
    """
    val = getattr(halo, halo_property, None)
    if val is None: val = halo[halo_property]
    return val

def _print_link_info(ds1, ds2):
    """
    Print information about linking datasets.
    """

    units = {"current_time": "Gyr"}
    for attr in ["basename", "current_time", "current_redshift"]:
        v1 = getattr(ds1, attr)
        v2 = getattr(ds2, attr)
        if attr in units:
            v1.convert_to_units(units[attr])
            v2.convert_to_units(units[attr])
        s = "Linking: %-20s = %-28s - %-28s" % (attr, v1, v2)
        mylog.info(s)
