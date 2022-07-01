"""
load function



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

from ytree.data_structures.arbor import \
    arbor_registry
from ytree.utilities.loading import \
    get_path

global load_warn
load_warn = True

def load(filename, method=None, **kwargs):
    """
    Load an Arbor, determine the type automatically.

    Parameters
    ----------
    filename : string
        Input filename.
    method : optional, string
        The type of Arbor to be loaded.  Existing types are:
        ConsistentTrees, Rockstar, TreeFarm, YTree.  If not
        given, the type will be determined based on characteristics
        of the input file.
    kwargs : optional, dict
        Additional keyword arguments are passed to _is_valid and
        the determined type.

    Returns
    -------
    Arbor

    Examples
    --------

    >>> import ytree
    >>> # saved Arbor (ytree format)
    >>> a = ytree.load("arbor/arbor.h5")
    >>> # Amiga Halo Finder
    >>> a = ytree.load("ahf_halos/snap_N64L16_000.parameter",
    ...                hubble_constant=0.7)
    >>> # consistent-trees
    >>> a = ytree.load("tiny_ctrees/locations.dat")
    >>> a = ytree.load("consistent_trees/tree_0_0_0.dat")
    >>> a = ytree.load("ctrees_hlists/hlists/hlist_0.12521.list")
    >>> # consistent-trees-hdf5
    >>> a = ytree.load("consistent_trees_hdf5/soa/forest.h5")
    >>> # LHaloTree
    >>> a = ytree.load("my_halos/trees_063.0")
    >>> # LHaloTree-hdf5
    >>> a = ytree.load("TNG50-4-Dark/trees_sf1_099.0.hdf5",
    ...                box_size=35, hubble_constant=0.6774,
    ...                omega_matter=0.3089, omega_lambda=0.6911)
    >>> # Moria
    >>> a = ytree.load("moria/moria_tree_testsim050.hdf5")
    >>> # Rockstar
    >>> a = ytree.load("rockstar_halos/out_0.list")
    >>> # treefarm
    >>> a = ytree.load("my_halos/fof_subhalo_tab_025.0.h5")
    >>> # TreeFrog
    >>> a = ytree.load("treefrog/VELOCIraptor.tree.t4.0-131.walkabletree.sage.forestID.foreststats.hdf5")

    """

    filename = get_path(filename)

    if method is None:
        candidates = []
        for candidate, c in arbor_registry.items():
            try:
                if c._is_valid(filename, **kwargs):
                    candidates.append(candidate)
            except BaseException:
                pass

        if len(candidates) == 0:
            raise IOError(f"Could not determine arbor type for {filename}.")
        elif len(candidates) > 1:
            errmsg = "Could not distinguish between these arbor types:\n"
            for candidate in candidates:
                errmsg += f"Possible: {candidate}.\n"
            errmsg += "Provide one of these types using the \"method\" keyword."
            raise IOError(errmsg)
        else:
            method = candidates[0]

    else:
        if method not in arbor_registry:
            raise IOError(
                f"Invalid method: {method}. Available: {arbor_registry.keys()}.")

    global load_warn
    if method not in ["YTree"] and load_warn:
        print(
f"""Additional features and improved performance (usually) by saving this arbor with \"save_arbor\" and reloading:
\t>>> a = ytree.load(\"{filename}\")
\t>>> fn = a.save_arbor()
\t>>> a = ytree.load(fn)"""
            )
        load_warn = False
    return arbor_registry[method](filename, **kwargs)
