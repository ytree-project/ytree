"""
Arbor class and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) 2016, Britton Smith <brittonsmith@gmail.com>
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

from collections import \
    defaultdict
import functools
import h5py
import glob
import numpy as np
import warnings
import yt

from yt.extern.six import \
    add_metaclass
from yt.frontends.ytdata.utilities import \
    save_as_dataset, \
    _hdf5_yt_array
from yt.funcs import \
    get_output_filename
from yt.units.unit_registry import \
    UnitRegistry
from yt.utilities.cosmology import \
    Cosmology

from ytree.tree_node import \
    TreeNode
from ytree.tree_node_selector import \
    tree_node_selector_registry
from ytree.utilities.io import \
    _hdf5_yt_attr

arbor_registry = {}

class RegisteredArbor(type):
    def __init__(cls, name, b, d):
        type.__init__(cls, name, b, d)
        arbor_type = name[:name.rfind("Arbor")]
        if arbor_type:
            arbor_registry[arbor_type] = cls

@add_metaclass(RegisteredArbor)
class Arbor(object):
    def __init__(self, filename):
        self.filename = filename
        self.unit_registry = UnitRegistry()
        self._load_trees()
        self._set_default_selector()
        self.cosmology = Cosmology(
            hubble_constant=self.hubble_constant,
            omega_matter=self.omega_matter,
            omega_lambda=self.omega_lambda,
            unit_registry=self.unit_registry)

    def set_selector(self, selector, *args, **kwargs):
        self.selector = tree_node_selector_registry.find(
            selector, *args, **kwargs)

    _arr = None
    @property
    def arr(self):
        if self._arr is not None:
            return self._arr
        self._arr = functools.partial(yt.YTArray, registry=self.unit_registry)
        return self._arr

    _quan = None
    @property
    def quan(self):
        if self._quan is not None:
            return self._quan
        self._quan = functools.partial(yt.YTQuantity, registry=self.unit_registry)
        return self._quan

    def _set_default_selector(self):
        for field in ["particle_mass", "mvir"]:
            if field in self._field_data:
                self.set_selector("max_field_value", field)

    def _set_halo_id_field(self):
        _hfields = ["halo_id", "particle_identifier"]
        hfields = [f for f in _hfields
                   if f in self._field_data]
        if len(hfields) == 0:
            raise RuntimeError("No halo id field found.")
        self._hid_field = hfields[0]

    def _load_trees(self):
        pass

    @classmethod
    def _is_valid(cls, *args, **kwargs):
        return False

    def save_arbor(self, filename=None, fields=None):
        filename = get_output_filename(filename, "arbor", ".h5")
        if fields is None:
            fields = self._field_data.keys()
        ds = {}
        for attr in ["hubble_constant",
                     "omega_matter",
                     "omega_lambda"]:
            if hasattr(self, attr):
                ds[attr] = getattr(self, attr)
        extra_attrs = {"box_size": self.box_size,
                       "arbor_type": "ArborArbor"}
        save_as_dataset(ds, filename, self._field_data,
                        extra_attrs=extra_attrs)
        return filename

class MonolithArbor(Arbor):
    def _load_field_data(self):
        pass

    def _load_trees(self):
        self._load_field_data()
        self._set_halo_id_field()

        self.trees = []
        all_uid = self._field_data["tree_id"]
        if hasattr(all_uid, "units"):
            all_uid = all_uid.d
        all_uid = all_uid.astype(np.int64)
        root_ids = np.unique(all_uid)
        pbar = yt.get_pbar("Loading trees", root_ids.size)
        for my_i, root_id in enumerate(root_ids):
            tree_halos = (root_id == self._field_data["tree_id"])
            my_tree = {}
            for i in np.where(tree_halos)[0]:
                desc_id = np.int64(self._field_data["desc_id"][i])
                halo_id = np.int64(self._field_data[self._hid_field][i])
                uid = np.int64(self._field_data["uid"][i])
                if desc_id == -1:
                    level = 0
                else:
                    level = my_tree[desc_id].level_id + 1
                my_node = TreeNode(halo_id, level, i, arbor=self)
                my_tree[uid] = my_node
                if desc_id >= 0:
                    my_tree[desc_id].add_ancestor(my_node)
            self.trees.append(my_tree[root_id])
            pbar.update(my_i)
        pbar.finish()
        yt.mylog.info("Arbor contains %d trees with %d total nodes." %
                      (len(self.trees), self._field_data["uid"].size))

class ArborArbor(MonolithArbor):
    def _load_field_data(self):
        fh = h5py.File(self.filename, "r")
        for attr in ["hubble_constant",
                     "omega_matter",
                     "omega_lambda"]:
            setattr(self, attr, fh.attrs[attr])
        self.unit_registry.modify("h", self.hubble_constant)
        self.box_size = _hdf5_yt_attr(fh, "box_size",
                                      unit_registry=self.unit_registry)
        self._field_data = dict([(f, _hdf5_yt_array(fh["data"], f, self))
                                 for f in fh["data"]])
        fh.close()

    @classmethod
    def _is_valid(self, *args, **kwargs):
        fn = args[0]
        if not fn.endswith(".h5"): return False
        try:
            with h5py.File(fn, "r") as f:
                if f.attrs.get("arbor_type") != "ArborArbor":
                    return False
        except:
            return False
        return True

_ct_columns = (("a",        (0,)),
               ("uid",      (1,)),
               ("desc_id",  (3,)),
               ("mvir",     (10,)),
               ("rvir",     (11,)),
               ("position", (17, 18, 19)),
               ("velocity", (20, 21, 21)),
               ("tree_id",  (29,)),
               ("halo_id",  (30,)), # from halo finder
               ("snapshot", (31,)))
_ct_units = {"mvir": "Msun/h",
             "rvir": "kpc/h",
             "position": "Mpc/h",
             "velocity": "km/s"}
_ct_usecol = []
_ct_fields = {}
for field, col in _ct_columns:
    _ct_usecol.extend(col)
    _ct_fields[field] = np.arange(len(_ct_usecol)-len(col),
                                  len(_ct_usecol))

class ConsistentTreesArbor(MonolithArbor):
    def _set_default_selector(self):
        self.set_selector("max_field_value", "mvir")

    def _read_cosmological_parameters(self):
        f = file(self.filename, "r")
        i = 0
        while True:
            i += 1
            line = f.readline()
            if line is None or not line.startswith("#"):
                break
            if "Omega_M" in line:
                pars = line[1:].split(";")
                for j, par in enumerate(["omega_matter",
                                         "omega_lambda",
                                         "hubble_constant"]):
                    v = float(pars[j].split(" = ")[1])
                    setattr(self, par, v)
            elif "Full box size" in line:
                pars = line.split("=")[1].strip().split()
                box = pars
        f.close()
        self._iheader = i
        self.unit_registry.modify("h", self.hubble_constant)
        self.box_size = self.quan(float(box[0]), box[1])

    def _load_field_data(self):
        yt.mylog.info("Loading tree data from %s." % self.filename)
        self._read_cosmological_parameters()
        data = np.loadtxt(self.filename, skiprows=self._iheader,
                          unpack=True, usecols=_ct_usecol)
        self._field_data = {}
        for field, cols in _ct_fields.items():
            if cols.size == 1:
                self._field_data[field] = data[cols][0]
            else:
                self._field_data[field] = np.rollaxis(data[cols], 1)
            if field in _ct_units:
                self._field_data[field] = \
                  self.arr(self._field_data[field], _ct_units[field])
        self._field_data["redshift"] = 1. / self._field_data["a"] - 1.
        del self._field_data["a"]

    @classmethod
    def _is_valid(self, *args, **kwargs):
        fn = args[0]
        if not fn.endswith(".dat"): return False
        with open(fn, "r") as f:
            valid = False
            while True:
                line = f.readline()
                if line is None or not line.startswith("#"):
                    break
                if "Consistent Trees" in line:
                    valid = True
                    break
            if not valid: return False
        return True

class CatalogArbor(Arbor):
    def _get_all_files(self):
        pass

    def _load_field_data(self, *args):
        pass

    def _to_field_array(self, field, data):
        if len(data) == 0:
            return np.array(data)
        if isinstance(data[0], yt.YTArray):
            self._field_data[field] = self.arr(data)
        else:
            self._field_data[field] = np.array(data)

    def _load_trees(self):
        my_files = self._get_all_files()
        self._field_data = defaultdict(list)

        offset = 0
        anc_ids = None
        anc_nodes = None
        my_trees = []
        pbar = yt.get_pbar("Load halo catalogs", len(my_files))
        for i, fn in enumerate(my_files):
            n_halos = self._load_field_data(fn, offset)
            if n_halos == 0:
                pbar.update(i)
                continue

            my_nodes = []
            for halo in range(n_halos):
                my_node = TreeNode(self._field_data["halo_id"][-1][halo], i,
                                   self._field_data["uid"][-1][halo], self)
                my_nodes.append(my_node)
                if self._field_data["desc_id"][-1][halo] == -1 or i == 0:
                    my_trees.append(my_node)

            if anc_ids is not None:
                des_ids = anc_ids
                des_nodes = anc_nodes
            anc_ids = self._field_data["halo_id"][-1]
            anc_nodes = my_nodes

            offset += n_halos
            if i == 0:
                pbar.update(i)
                continue

            for halo in range(n_halos):
                des_id = self._field_data["desc_id"][-1][halo]
                if des_id == -1: continue
                i_des = np.where(des_id == des_ids)[0][0]
                des_nodes[i_des].add_ancestor(anc_nodes[halo])

            pbar.update(i)
        pbar.finish()
        self.trees = my_trees

        for field in self._field_data:
            my_data = []
            for level in self._field_data[field]:
                my_data.extend(level)
            self._to_field_array(field, my_data)

        self._field_data["tree_id"] = -np.ones(offset)
        for t in self.trees:
            self._field_data["tree_id"][t._tree_field_indices] = t["uid"]
            for tnode in t.twalk():
                if tnode.ancestors is None: continue
                for a in tnode.ancestors:
                    self._field_data["desc_id"][a.global_id] = tnode["uid"]
        assert (self._field_data["tree_id"] != -1).any()

        yt.mylog.info("Arbor contains %d trees with %d total nodes." %
                      (len(self.trees), offset))

_rs_columns = (("halo_id",  (0,)),
               ("desc_id",  (1,)),
               ("mvir",     (2,)),
               ("rvir",     (5,)),
               ("position", (8, 9, 10)),
               ("velocity", (11, 12, 13)))
_rs_units = {"mvir": "Msun/h",
             "rvir": "kpc/h",
             "position": "Mpc/h",
             "velocity": "km/s"}
_rs_type = {"halo_id": np.int64,
            "desc_id": np.int64}
_rs_usecol = []
_rs_fields = {}
for field, col in _rs_columns:
    _rs_usecol.extend(col)
    _rs_fields[field] = np.arange(len(_rs_usecol)-len(col),
                                  len(_rs_usecol))

class RockstarArbor(CatalogArbor):
    def _get_all_files(self):
        prefix = self.filename.rsplit("_", 1)[0]
        suffix = ".list"
        my_files = glob.glob("%s_*%s" % (prefix, suffix))
        # sort by catalog number
        my_files.sort(key=lambda x:
                      int(x[x.find(prefix)+len(prefix)+1:x.rfind(suffix)]),
                      reverse=True)
        return my_files

    def _to_field_array(self, field, data):
        if field in _rs_units:
            self._field_data[field] = self.arr(data, _rs_units[field])
        else:
            self._field_data[field] = np.array(data)

    def _read_parameters(self, filename):
        get_pars = not hasattr(self, "hubble_constant")
        f = file(filename, "r")
        while True:
            line = f.readline()
            if line is None or not line.startswith("#"):
                break
            if get_pars and line.startswith("#Om = "):
                pars = line[1:].split(";")
                for j, par in enumerate(["omega_matter",
                                         "omega_lambda",
                                         "hubble_constant"]):
                    v = float(pars[j].split(" = ")[1])
                    setattr(self, par, v)
            if get_pars and line.startswith("#Box size:"):
                pars = line.split(":")[1].strip().split()
                box = pars
            if line.startswith("#a = "):
                a = float(line.split("=")[1].strip())
        f.close()
        if get_pars:
            self.unit_registry.modify("h", self.hubble_constant)
            self.box_size = self.quan(float(box[0]), box[1])
        return 1. / a - 1.

    def _load_field_data(self, fn, offset):
        with warnings.catch_warnings():
            # silence empty file warnings
            warnings.simplefilter("ignore", category=UserWarning,
                                  append=1, lineno=893)
            data = np.loadtxt(fn, unpack=True, usecols=_rs_usecol)
        z = self._read_parameters(fn)
        if data.size == 0:
            return 0

        if len(data.shape) == 1:
            data = np.reshape(data, (data.size, 1))
        n_halos = data.shape[1]
        self._field_data["redshift"].append(z * np.ones(n_halos))
        self._field_data["uid"].append(np.arange(offset, offset+n_halos))
        for field, cols in _rs_fields.items():
            if cols.size == 1:
                self._field_data[field].append(data[cols][0])
            else:
                self._field_data[field].append(np.rollaxis(data[cols], 1))
            if field in _rs_type:
                self._field_data[field][-1] = \
                  self._field_data[field][-1].astype(_rs_type[field])
        return n_halos

    @classmethod
    def _is_valid(self, *args, **kwargs):
        fn = args[0]
        if not fn.endswith(".list"): return False
        return True

class TreeFarmArbor(CatalogArbor):
    def _set_default_selector(self):
        self.set_selector("max_field_value", "particle_mass")

    def _get_all_files(self):
        prefix = self.filename.rsplit("_", 1)[0]
        suffix = ".h5"
        my_files = glob.glob("%s_*%s" % (prefix, suffix))
        # sort by catalog number
        my_files.sort(key=lambda x:
                      int(x[x.find(prefix)+len(prefix)+1:x.find(".0")]),
                      reverse=True)
        return my_files

    def _load_field_data(self, fn, offset):
        ds = yt.load(fn)

        if not hasattr(self, "hubble_constant"):
            for attr in ["hubble_constant",
                         "omega_matter",
                         "omega_lambda"]:
                setattr(self, attr, getattr(ds, attr))
            self.unit_registry.modify("h", self.hubble_constant)
            self.box_size = ds.domain_width[0]
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
            self._field_data[field[1]].append(ds.r[field].in_base())
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
        fn = args[0]
        if not fn.endswith(".h5"): return False
        try:
            with h5py.File(fn, "r") as f:
                if f.attrs.get("data_type") != "halo_catalog":
                    return False
        except:
            return False
        return True

def load(filename, method=None):
    if method is None:
        candidates = []
        for candidate, c in arbor_registry.items():
            if c._is_valid(filename):
                candidates.append(candidate)
        if len(candidates) == 0:
            yt.mylog.error("Could not determine arbor type for %s." % filename)
            raise RuntimeError
        elif len(candidates) > 1:
            yt.mylog.error("Could not distinguish between these arbor types:")
            for candidate in candidates:
                yt.mylog.error("Possible: %s." % candidate)
            yt.mylog.error("Provide one of these types using the \'method\' keyword.")
            raise RuntimeError
        else:
            method = candidates[0]
    else:
        if method not in arbor_registry:
            raise RuntimeError("Invalid method: %s.  Available: %s." %
                               (method, arbor_registry.keys()))
    return arbor_registry[method](filename)
