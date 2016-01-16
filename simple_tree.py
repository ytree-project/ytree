import numpy as np
import yt

from yt.utilities.exceptions import \
    YTSphereTooSmall

def halos_in_sphere(hc, ds2, radius_field, factor=1):
    radius = (factor * hc[radius_field]).in_units("code_length")
    try:
        sp = ds2.sphere(hc.position.in_units("code_length"), radius)
        my_ids = sp[(hc.ptype, "particle_identifier")]
        return my_ids.d.astype(np.int64)
    except YTSphereTooSmall:
        return []

def simple_ancestry(hc, candidate):
    threshold = 0.5
    hc_ids = hc["member_ids"]
    c_ids = candidate["member_ids"]
    common = np.intersect1d(hc_ids, c_ids)
    return common.size > threshold * c_ids.size

class SimpleTree(object):
    def __init__(self, time_series):
        self.ts = time_series

    def find_ancestors(self, halo_type, halo_id, ds1, ds2):
        ancestors = []
        hc = ds1.halo(halo_type, halo_id)
        candidate_ids = halos_in_sphere(hc, ds2, "Group_R_Crit200", 5)
        for candidate_id in candidate_ids:
            candidate = ds2.halo(hc.ptype, candidate_id)
            if simple_ancestry(hc, candidate):
                ancestors.append(candidate_id)
        return ancestors

    def trace_lineage(self, halo_type, halo_ids):
        outputs_r = self.ts.outputs[::-1]
        ds1 = yt.load(outputs_r[0])
        halo_info = {"redshift": ds1.current_redshift,
                     "ds": ds1.parameter_filename}
        current_ids = halo_ids

        all_ancestor_ids = []
        all_descendent_ids = []

        for fn in outputs_r[1:]:
            ds2 = yt.load(fn)

            yt.mylog.info("Searching for ancestors of %d halos." %
                          len(current_ids))

            halo_info["redshift"] = ds2.current_redshift
            halo_info["ds"] = ds2.parameter_filename

            these_ancestor_ids = []
            these_descendent_ids = []

            for current_id in current_ids:
                ancestor_ids = self.find_ancestors(
                    halo_type, current_id, ds1, ds2)
                these_ancestor_ids.extend(ancestor_ids)
                these_descendent_ids.extend(
                    [current_id]*len(ancestor_ids))

            all_ancestor_ids.append(these_ancestor_ids)
            all_descendent_ids.append(these_descendent_ids)

            ds1 = ds2
            current_ids = these_ancestor_ids
            if len(current_ids) == 0:
                break

        return # need to return something
