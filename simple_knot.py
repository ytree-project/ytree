import numpy as np
import yt

class SimpleKnot(object):
    def __init__(self, halo_id, properties=None):
        self.halo_id = halo_id
        self.ancestors = []
        if properties is None: properties = {}
        for p, val in properties.items():
            setattr(self, p, val)

    def __repr__(self):
        return "SimpleKnot[%d]" % self.halo_id

def load_tree(filename, properties=None):
    ds = yt.load(filename)
    if properties is None: properties = {}

    halo_ids = ds.data["halo_ids"].d.astype(np.int64)
    ancestor_counts = ds.data["ancestor_counts"].d.astype(np.int64)

    # 1) Get the number of ancestors on each level.
    level_count = []
    i_count = 0
    knots_on_level = 1
    while (i_count < ancestor_counts.size):
        level_count.append(ancestor_counts[i_count:i_count+knots_on_level])
        i_count += knots_on_level
        knots_on_level = level_count[-1].sum()

    # 2) Create level arrays full of knots.
    i_halo = 0
    level_knots = []
    for i_level, level in enumerate(level_count):
        level_knots.append([])
        for i_on_level in range(sum(level)):
            halo_properties = dict([(hp, ds.data[hp][i_halo])
                                    for hp in properties])
            halo_properties["redshift"] = ds.data["redshift"][i_level]
            my_id = halo_ids[i_halo]
            level_knots[-1].append(SimpleKnot(halo_ids[i_halo],
                                              halo_properties))
            i_halo += 1
    level_count.pop(0)

    # 3) Assemble tree structure.
    for i_level, knots in enumerate(level_knots[:-1]):
        i_anc = 0
        for i_knot, knot in enumerate(knots):
            n_anc = level_count[i_level][i_knot]
            knot.ancestors = level_knots[i_level+1][i_anc:i_anc+n_anc]
            i_anc += n_anc
    
    my_tree = level_knots.pop(0)
    del level_knots
    return my_tree
