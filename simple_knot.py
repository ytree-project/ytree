import h5py
import glob
import numpy as np
import os
import yt

class TreeNode(object):
    def __init__(self, halo_id, level_id=None):
        self.halo_id = halo_id
        self.level_id = level_id
        self.ancestors = None

    def add_ancestor(self, ancestor):
        if self.ancestors is None:
            self.ancestors = []
        self.ancestors.append(ancestor)

    def __repr__(self):
        if self.level_id is None:
            return "TreeNode[%d]" % self.halo_id
        else:
            return "TreeNode[%d,%d]" % (self.level_id, self.halo_id)

def get_ancestry_arrays(knot, fields):
    data = dict([(field, []) for field in fields])
    my_knot = knot
    while my_knot is not None:
        for field in fields:
            data[field].append(getattr(my_knot, field))
        if my_knot.ancestors is not None and \
          len(my_knot.ancestors) > 0:
            my_knot = my_knot.ancestors[0]
        else:
            my_knot = None
    for field in data:
        data[field] = yt.YTArray(data[field])
    return data

def load_tree(output_dir, properties=None):
    my_files = glob.glob(os.path.join(output_dir, "tree_segment_*.h5"))
    my_files.sort()
    if properties is None: properties = {}

    my_tree = None
    for i, fn in enumerate(my_files):
        fh = h5py.File(fn, "r")
        if my_tree is None:
            des_ids = fh["data/descendent_particle_identifier"].value
        else:
            des_ids = anc_ids
        anc_ids = fh["data/ancestor_particle_identifier"].value
        links = fh["data/links"].value
        fh.close()

        if my_tree is None:
            des_nodes = [TreeNode(my_id, i) for my_id in des_ids]
            my_tree = des_nodes
        else:
            des_nodes = anc_nodes

        anc_nodes = [TreeNode(my_id, i+1) for my_id in anc_ids]

        for link in links:
            i_des = np.where(link[0] == des_ids)[0][0]
            i_anc = np.where(link[1] == anc_ids)[0][0]
            des_nodes[i_des].add_ancestor(anc_nodes[i_anc])

    return my_tree
