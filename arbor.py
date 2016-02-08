import h5py
import glob
import numpy as np
import os
import yt

from yt.frontends.ytdata.utilities import \
    _hdf5_yt_array

class TreeNode(object):
    def __init__(self, halo_id, level_id, global_id=None):
        self.halo_id = halo_id
        self.level_id = level_id
        self.global_id = global_id
        self.ancestors = None

    def add_ancestor(self, ancestor):
        if self.ancestors is None:
            self.ancestors = []
        self.ancestors.append(ancestor)

    def __repr__(self):
        return "TreeNode[%d,%d]" % (self.level_id, self.halo_id)

class Tree(object):
    def __init__(self, trunk, arbor=None):
        self.trunk = trunk
        self.arbor = arbor

    def __repr__(self):
        return "%s" % self.trunk

    def __getitem__(self, field):
        field_ids = []
        my_node = self.trunk
        while my_node is not None:
            field_ids.append(my_node.global_id)
            if my_node.ancestors is None:
                my_node = None
            else:
                my_node = my_node.ancestors[0]
        field_ids = np.array(field_ids)
        return self.arbor._field_data[field][field_ids]

class Arbor(object):
    def __init__(self, output_dir, fields=None):
        self.output_dir = output_dir
        if fields is None:
            fields = []
        self.fields = fields
        self._load_tree()

    def _load_tree(self):
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
                des_nodes = [TreeNode(my_id, i, gid+offset)
                             for gid, my_id in enumerate(des_ids)]
                my_trees = des_nodes
                offset += des_ids.size
            else:
                des_nodes = anc_nodes

            anc_nodes = [TreeNode(my_id, i+1, gid+offset)
                         for gid, my_id in enumerate(anc_ids)]
            offset += anc_ids.size

            for link in links:
                i_des = np.where(link[0] == des_ids)[0][0]
                i_anc = np.where(link[1] == anc_ids)[0][0]
                des_nodes[i_des].add_ancestor(anc_nodes[i_anc])
            pbar.update(i)
        pbar.finish()

        self.redshift = np.array(self.redshift)
        self.trees = [Tree(trunk, self) for trunk in my_trees]

        for field in self._field_data:
            pbar = yt.get_pbar("Preparing mass data",
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
