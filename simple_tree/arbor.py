import functools
import h5py
import glob
import numpy as np
import os
import yt

from yt.frontends.ytdata.utilities import \
    _hdf5_yt_array
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
        self._field_ids = None
        self._tree_line = None

    def add_ancestor(self, ancestor):
        if self.ancestors is None:
            self.ancestors = []
        self.ancestors.append(ancestor)

    def halo(self, field):
        return self.arbor._field_data[field][self.global_id]

    def __repr__(self):
        return "TreeNode[%d,%d]" % (self.level_id, self.halo_id)

    def __getitem__(self, field):
        if self._field_ids is None:
            field_ids = []
            tree_line = []
            my_node = self
            while my_node is not None:
                field_ids.append(my_node.global_id)
                tree_line.append(my_node)
                if my_node.ancestors is None:
                    my_node = None
                else:
                    my_node = my_node.arbor.selector(my_node.ancestors)
            self._field_ids = np.array(field_ids)
            self._tree_line = tree_line
        if isinstance(field, str):
            return self.arbor._field_data[field][self._field_ids]
        else:
            return self._tree_line[field]

class Arbor(object):
    def __init__(self):
        self.unit_registry = UnitRegistry()

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
    def __init__(self, filename):
        super(ArborCT, self).__init__()
        self.filename = filename
        self._read_cosmological_parameters()
        self.unit_registry.modify("h", self.hubble_constant)
        self.cosmology = Cosmology(
            hubble_constant=self.hubble_constant,
            omega_matter=self.omega_matter,
            omega_lambda=self.omega_lambda,
            unit_registry=self.unit_registry)

        self._load_field_data()
        self._load_trees()
        for field in ["tree_id", "desc_id", "halo_id", "uid"]:
            del self._field_data[field]
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
        self.trees = []
        root_ids = np.unique(self._field_data["tree_id"])
        pbar = yt.get_pbar("Loading trees", root_ids.size)
        for my_i, root_id in enumerate(root_ids):
            tree_halos = (root_id == self._field_data["tree_id"])
            my_tree = {}
            for i in np.where(tree_halos)[0]:
                desc_id = int(self._field_data["desc_id"][i])
                halo_id = int(self._field_data["halo_id"][i])
                uid = int(self._field_data["uid"][i])
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
        yt.mylog.info("Arbor contains %d trees with %d total halos." %
                      (len(self.trees), self._field_data["uid"].size))

class ArborTF(Arbor):
    def __init__(self, output_dir, fields=None):
        super(ArborTF, self).__init__()
        self.output_dir = output_dir
        if fields is None:
            fields = []
        self.fields = fields
        self._load_trees()
        self.set_selector("max_field_value", "mass")

    def _load_trees(self):
        my_files = glob.glob(os.path.join(self.output_dir, "tree_segment_*.h5"))
        my_files.sort()

        self._field_data = dict([(f, []) for f in self.fields])
        self.redshift = []

        offset = 0
        my_trees = None
        pbar = yt.get_pbar("Load segment files", len(my_files))
        for i, fn in enumerate(my_files):
            fh = h5py.File(fn, "r")
            if my_trees is None:
                self.redshift.append(fh.attrs["descendent_current_redshift"])
                des_ids = fh["data/descendent_particle_identifier"].value
                for field in self.fields:
                    self._field_data[field].append(
                        _hdf5_yt_array(fh, "data/descendent_%s" % field))
            else:
                des_ids = anc_ids
            self.redshift.append(fh.attrs["ancestor_current_redshift"])
            anc_ids = fh["data/ancestor_particle_identifier"].value
            for field in self.fields:
                self._field_data[field].append(
                    _hdf5_yt_array(fh, "data/ancestor_%s" % field))
            links = fh["data/links"].value
            fh.close()

            if my_trees is None:
                des_nodes = [TreeNode(my_id, i, gid+offset, arbor=self)
                             for gid, my_id in enumerate(des_ids)]
                my_trees = des_nodes
                offset += des_ids.size
            else:
                des_nodes = anc_nodes

            anc_nodes = [TreeNode(my_id, i+1, gid+offset, arbor=self)
                         for gid, my_id in enumerate(anc_ids)]
            offset += anc_ids.size

            for link in links:
                i_des = np.where(link[0] == des_ids)[0][0]
                i_anc = np.where(link[1] == anc_ids)[0][0]
                des_nodes[i_des].add_ancestor(anc_nodes[i_anc])
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

        yt.mylog.info("Arbor contains %d trees with %d total halos." %
                      (len(self.trees), offset))
