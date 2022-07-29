import numpy as np
import yt
yt.enable_parallelism()
import ytree

def calc_a50(node):
    # main progenitor masses
    pmass = node["prog", "mass"]

    mh = 0.5 * node["mass"]
    m50 = pmass <= mh

    if not m50.any():
        th = node["scale_factor"]
    else:
        pscale = node["prog", "scale_factor"]
        # linearly interpolate
        i = np.where(m50)[0][0]
        slope = (pscale[i-1] - pscale[i]) / (pmass[i-1] - pmass[i])
        th = slope * (mh - pmass[i]) + pscale[i]

    node["a50"] = th


a = ytree.load("tiny_ctrees/locations.dat")
a.add_analysis_field("a50", "")

ap = ytree.AnalysisPipeline()
ap.add_operation(calc_a50)

trees = list(a[:])
for tree in ytree.parallel_nodes(trees, filename="halo_age"):
    yt.mylog.info(f"Processing {tree}.")
    ap.process_target(tree)

if yt.is_root():
    a2 = ytree.load("halo_age/halo_age.h5")
    print (a2[0]["a50"])
