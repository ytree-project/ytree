"""
Calculate merger and smooth accretion rates for each halo in the dataset.

The growth rate of a halo is decomposed into two components:
- Merger rate: mass gained from merging with other halos
- Smooth accretion rate: mass gained from diffuse accretion

For each halo node, the rates are computed as:
    merger_rate = (sum of all progenitor masses - main progenitor mass) / dt
    smooth_accretion_rate = (total mass change - merger contribution) / dt

NOTE: this script includes extra code to make it run within
the test suite. To run conventionally, remove the following
lines and return the code block in the middle to the proper
tabbing (i.e., 4 spaces to the left).

    from mpi4py import MPI
    comm = MPI.Comm.Get_parent()
    try:

    except BaseException:
        pass
    comm.Barrier()
    comm.Disconnect()

"""

import ytree
import yt

yt.enable_parallelism()


def calc_accretion_rates(node):
    ancestors = list(node.ancestors)
    if not ancestors:
        return

    try:
        main_prog = list(node["prog"])[1]
    except IndexError:
        return

    dt = node["time"].to("yr") - main_prog["time"].to("yr")
    if dt == 0:
        return

    dm_total = node["mass"] - main_prog["mass"]
    m_all_progs = sum(p["mass"] for p in ancestors)
    dm_merger = m_all_progs - main_prog["mass"]

    node["mdot_merger"] = dm_merger / dt
    node["mdot_accretion"] = (dm_total - dm_merger) / dt


if __name__ == "__main__":
    # Remove the next three and final four lines to run conventionally.
    from mpi4py import MPI

    comm = MPI.Comm.Get_parent()
    try:
        a = ytree.load("tiny_ctrees/locations.dat")
        a.add_analysis_field("mdot_merger", units="Msun/yr", default=0.)
        a.add_analysis_field("mdot_accretion", units="Msun/yr", default=0.)

        ap = ytree.AnalysisPipeline()
        ap.add_operation(calc_accretion_rates)

        trees = list(a[:])
        for tree in ytree.parallel_nodes(trees, filename="accretion_rates"):
            yt.mylog.info(f"Processing {tree}.")
            ap.process_target(tree)

        if yt.is_root():
            a2 = ytree.load("accretion_rates/accretion_rates.h5")
            print(a2[0]["mdot_merger"])
            print(a2[0]["mdot_accretion"])

    # Remove the next four lines to run conventionally.
    except BaseException:
        pass
    comm.Barrier()
    comm.Disconnect()
