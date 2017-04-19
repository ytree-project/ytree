"""
TreeFarmArbor class and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) 2016, Britton Smith <brittonsmith@gmail.com>
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

from ytree.arbor.arbor import \
    CatalogArbor

class TreeFarmArbor(CatalogArbor):
    """
    Class for Arbors created with :class:`~ytree.tree_farm.TreeFarm`.
    """
    def _set_default_selector(self):
        """
        Mass is "particle_mass".
        """
        self.set_selector("max_field_value", "particle_mass")

    def _get_all_files(self):
        """
        Get all files and put in reverse order.
        """
        prefix = self.filename.rsplit("_", 1)[0]
        suffix = ".h5"
        my_files = glob.glob("%s_*%s" % (prefix, suffix))
        # sort by catalog number
        my_files.sort(key=lambda x:
                      int(x[x.find(prefix)+len(prefix)+1:x.find(".0")]),
                      reverse=True)
        return my_files

    def _load_field_data(self, fn, offset):
        """
        Load field data as a yt HaloCatalog dataset.
        Get cosmological parameters and modify unit registry
        for hubble constant.
        Create a redshift field and uid field and rename
        particle_identifier and descendent_identifier to halo_id
        and desc_id.
        """
        ds = yt_load(fn)

        if not hasattr(self, "hubble_constant"):
            for attr in ["hubble_constant",
                         "omega_matter",
                         "omega_lambda"]:
                setattr(self, attr, getattr(ds, attr))
            # Drop the "cm" suffix because all lengths will
            # be in comoving units.
            self.box_size = self.quan(
                ds.domain_width[0].to("Mpccm/h"), "Mpc/h")
        try:
            if len(ds.field_list) == 0 or ds.index.total_particles == 0:
                return 0
        except ValueError:
            return 0
        skip_fields = ["particle_identifier", "descendent_identifier"]
        add_fields = [("halos", field)
                      for field in ["particle_position",
                                    "particle_velocity"]]
        for field in ds.field_list + add_fields:
            if field[0] != "halos": continue
            if "particle_position_" in field[1]: continue
            if "particle_velocity_" in field[1]: continue
            if field[1] in skip_fields: continue
            field_data = ds.r[field]
            if field_data.units.dimensions is length:
                field_data.convert_to_units("unitary")
            self._field_data[field[1]].append(field_data)
        self._field_data["halo_id"].append(
          ds.r["halos", "particle_identifier"].d.astype(np.int64))
        self._field_data["desc_id"].append(
          ds.r["halos", "descendent_identifier"].d.astype(np.int64))
        n_halos = self._field_data["halo_id"][-1].size
        self._field_data["redshift"].append(
            ds.current_redshift * np.ones(n_halos))
        self._field_data["uid"].append(
            np.arange(offset, offset+n_halos))
        return n_halos

    @classmethod
    def _is_valid(self, *args, **kwargs):
        """
        File should end in .h5, be loadable as an hdf5 file,
        and have a "data_type" attribute.
        """
        fn = args[0]
        if not fn.endswith(".h5"): return False
        try:
            with h5py.File(fn, "r") as f:
                if "data_type" not in f.attrs:
                    return False
                if f.attrs["data_type"].astype(str) != "halo_catalog":
                    return False
        except:
            return False
        return True
