import h5py
import glob
import numpy as np
import os
import yt

class SimpleKnot(object):
    def __init__(self, halo_id, properties=None):
        self.halo_id = halo_id
        self.ancestors = None
        if properties is None: properties = {}
        for p, val in properties.items():
            setattr(self, p, val)

    def __repr__(self):
        return "SimpleKnot[%d]" % self.halo_id

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

    
