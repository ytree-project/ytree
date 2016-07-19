import functools
import h5py
import glob
import numpy as np
import os
import yt

from yt.extern.six import \
    string_types
from yt.frontends.ytdata.utilities import \
    save_as_dataset, \
    _hdf5_yt_array
from yt.funcs import \
    get_output_filename
from yt.units.unit_registry import \
    UnitRegistry
from yt.utilities.cosmology import \
    Cosmology

from .tree_node_selector import \
    tree_node_selector_registry

class TreeNode(object):
    def __init__(self, halo_id, level_id, global_id=None, arbor=None):
        self.halo_id = halo_id
        self.level_id = level_id
        self.global_id = global_id
        self.ancestors = None
        self.arbor = arbor

    def add_ancestor(self, ancestor):
        if self.ancestors is None:
            self.ancestors = []
        self.ancestors.append(ancestor)

    def __getitem__(self, field):
        return self.arbor._field_data[field][self.global_id]

    def __repr__(self):
        return "TreeNode[%d,%d]" % (self.level_id, self.halo_id)

    _tfi = None
    @property
    def _tree_field_indices(self):
        if self._tfi is None:
            self._set_tree_attrs()
        return self._tfi

    _tn = None
    @property
    def _tree_nodes(self):
        if self._tn is None:
            self._set_tree_attrs()
        return self._tn

    def _set_tree_attrs(self):
        tfi = []
        tn = []
        for my_node in self.twalk():
            tfi.append(my_node.global_id)
            tn.append(my_node)
        self._tfi = np.array(tfi)
        self._tn = tn

    _lfi = None
    @property
    def _line_field_indices(self):
        if self._lfi is None:
            self._set_line_attrs()
        return self._lfi

    _ln = None
    @property
    def _line_nodes(self):
        if self._ln is None:
            self._set_line_attrs()
        return self._ln

    def _set_line_attrs(self):
        lfi = []
        ln = []
        for my_node in self.lwalk():
            lfi.append(my_node.global_id)
            ln.append(my_node)
        self._lfi = np.array(lfi)
        self._ln = ln

    def twalk(self):
        yield self
        if self.ancestors is None:
            return
        for ancestor in self.ancestors:
            for a_node in ancestor.twalk():
                yield a_node

    def lwalk(self):
        my_node = self
        while my_node is not None:
            yield my_node
            if my_node.ancestors is None:
                my_node = None
            else:
                my_node = my_node.arbor.selector(my_node.ancestors)

    def tree(self, field):
        if isinstance(field, string_types):
            return self.arbor._field_data[field][self._tree_field_indices]
        else:
            return self._tree_nodes[field]

    def line(self, field):
        if isinstance(field, string_types):
            return self.arbor._field_data[field][self._line_field_indices]
        else:
            return self._line_nodes[field]

    def save_tree(self, filename=None, fields=None):
        keyword = "tree_%d_%d" % (self.level_id, self.halo_id)
        filename = get_output_filename(filename, keyword, ".h5")
        if fields is None:
            fields = self.arbor._field_data.keys()
        ds = {}
        for attr in ["hubble_constant",
                     "omega_matter",
                     "omega_lambda"]:
            if hasattr(self.arbor, attr):
                ds[attr] = getattr(self.arbor, attr)
        data = {}
        for field in fields:
            data[field] = self.tree(field)
        save_as_dataset(ds, filename, data)
        return filename

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

    def _set_default_selector(self):
        pass

    def _load_trees(self):
        pass

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

class ArborCT(Arbor):
    def _set_default_selector(self):
        self.set_selector("max_field_value", "mvir")

    def _read_cosmological_parameters(self):
        f = file(self.filename, "r")
        for i in range(2):
            line = f.readline()
        f.close()
        pars = line[1:].split(";")
        for i, par in enumerate(["omega_matter", "omega_lambda",
                                 "hubble_constant"]):
            v = float(pars[i].split(" = ")[1])
            setattr(self, par, v)

    def _load_field_data(self):
        yt.mylog.info("Loading tree data from %s." % self.filename)
        self._read_cosmological_parameters()
        self.unit_registry.modify("h", self.hubble_constant)
        data = np.loadtxt(self.filename, skiprows=46, unpack=True,
                          usecols=_ct_usecol)
        self._field_data = {}
        for field, cols in _ct_fields.items():
            if cols.size == 1:
                self._field_data[field] = data[cols][0]
            else:
                self._field_data[field] = np.rollaxis(data[cols], 1)
            if field in _ct_units:
                self._field_data[field] = \
                  yt.YTArray(self._field_data[field], _ct_units[field],
                             registry=self.unit_registry)
        self._field_data["redshift"] = 1. / self._field_data["a"] - 1.
        del self._field_data["a"]

    def _load_trees(self):
        self._load_field_data()

        self.trees = []
        root_ids = np.unique(self._field_data["tree_id"])
        pbar = yt.get_pbar("Loading trees", root_ids.size)
        for my_i, root_id in enumerate(root_ids):
            tree_halos = (root_id == self._field_data["tree_id"])
            my_tree = {}
            for i in np.where(tree_halos)[0]:
                desc_id = np.int64(self._field_data["desc_id"][i])
                halo_id = np.int64(self._field_data["halo_id"][i])
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

class ArborTF(Arbor):
    def _set_default_selector(self):
        self.set_selector("max_field_value", "mass")

    def _load_trees(self):
        my_files = glob.glob(os.path.join(self.filename, "tree_segment_*.h5"))
        my_files.sort()

        fields = None
        self._field_data = \
          dict([(f, []) for f in ["uid", "desc_id", "tree_id"]])
        self.redshift = []

        offset = 0
        my_trees = None
        pbar = yt.get_pbar("Load segment files", len(my_files))
        for i, fn in enumerate(my_files):
            fh = h5py.File(fn, "r")
            if fields is None:
                for attr in ["omega_matter", "omega_lambda",
                             "hubble_constant"]:
                    setattr(self, attr, fh.attrs[attr])
                self.unit_registry.modify("h", self.hubble_constant)

                fields = []
                for field in fh["data"]:
                    if field.startswith("descendent_"):
                        fields.append(field[len("descendent_"):])
                self._field_data.update(dict([(f, []) for f in fields]))

            if my_trees is None:
                self.redshift.append(fh.attrs["descendent_current_redshift"])
                des_ids = fh["data/descendent_particle_identifier"].value
                for field in fields:
                    self._field_data[field].append(
                        _hdf5_yt_array(fh, "data/descendent_%s" % field))
            else:
                des_ids = anc_ids

            self.redshift.append(fh.attrs["ancestor_current_redshift"])
            anc_ids = fh["data/ancestor_particle_identifier"].value
            for field in fields:
                self._field_data[field].append(
                    _hdf5_yt_array(fh, "data/ancestor_%s" % field))
            links = fh["data/links"].value
            fh.close()

            if my_trees is None:
                fsize = des_ids.size
                self._field_data["uid"].append(
                    np.arange(offset, offset + fsize, dtype=np.int64))
                self._field_data["desc_id"].append(
                    -np.ones(fsize, dtype=np.int64))
                self._field_data["tree_id"].append(
                    self._field_data["uid"][0])
                des_nodes = [TreeNode(my_id, i, gid+offset, arbor=self)
                             for gid, my_id in enumerate(des_ids)]
                my_trees = des_nodes
                offset += fsize
            else:
                des_nodes = anc_nodes

            fsize = anc_ids.size
            self._field_data["uid"].append(
                np.arange(offset, offset + fsize, dtype=np.int64))
            self._field_data["desc_id"].append(
                -np.ones(fsize, dtype=np.int64))
            self._field_data["tree_id"].append(
                -np.ones(fsize, dtype=np.int64))
            anc_nodes = [TreeNode(my_id, i+1, gid+offset, arbor=self)
                         for gid, my_id in enumerate(anc_ids)]
            offset += fsize

            for link in links:
                i_des = np.where(link[0] == des_ids)[0][0]
                i_anc = np.where(link[1] == anc_ids)[0][0]
                des_nodes[i_des].add_ancestor(anc_nodes[i_anc])
                self._field_data["desc_id"][-1][i_anc] = \
                  self._field_data["uid"][-2][i_des]
                self._field_data["tree_id"][-1][i_anc] = \
                  self._field_data["tree_id"][-2][i_des]
            pbar.update(i)
        pbar.finish()

        self.redshift = np.array(self.redshift)
        self.trees = my_trees

        for field in self._field_data:
            pbar = yt.get_pbar("Preparing %s data" % field,
                               len(self._field_data[field]))
            my_data = []
            for i, level in enumerate(self._field_data[field]):
                my_data.extend(level)
                pbar.update(i)
            if hasattr(my_data[0], "units"):
                my_data = yt.YTArray(my_data)
            else:
                my_data = np.array(my_data)
            self._field_data[field] = my_data
            pbar.finish()

        yt.mylog.info("Arbor contains %d trees with %d total nodes." %
                      (len(self.trees), offset))

class ArborST(Arbor):
    def _set_default_selector(self):
        for field in ["mass", "mvir"]:
            if field in self._field_data:
                self.set_selector("max_field_value", "mvir")

    def _load_field_data(self):
        fh = h5py.File(self.filename, "r")
        for attr in ["hubble_constant",
                     "omega_matter",
                     "omega_lambda"]:
            setattr(self, attr, fh.attrs[attr])
        self.unit_registry.modify("h", self.hubble_constant)
        self._field_data = dict([(f, _hdf5_yt_array(fh["data"], f, self))
                                 for f in fh["data"]])
        fh.close()

    def _load_trees(self):
        self._load_field_data()

        self.trees = []
        hfield = None
        _hfields = ["halo_id", "particle_identifier"]
        root_ids = np.unique(self._field_data["tree_id"]).d.astype(np.int64)
        pbar = yt.get_pbar("Loading trees", root_ids.size)
        for my_i, root_id in enumerate(root_ids):
            tree_halos = (root_id == self._field_data["tree_id"])
            my_tree = {}
            for i in np.where(tree_halos)[0]:
                desc_id = np.int64(self._field_data["desc_id"][i])
                if hfield is None:
                    hfields = [f for f in _hfields
                               if f in self._field_data]
                    if len(hfields) == 0:
                        raise RuntimeError("No halo id field found.")
                    hfield = hfields[0]
                halo_id = np.int64(self._field_data[hfield][i])
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
