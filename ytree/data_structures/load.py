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

import os

from ytree.data_structures.arbor import \
    arbor_registry

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
    >>> # saved Arbor
    >>> a = ytree.load("arbor/arbor.h5")
    >>> # consistent-trees output
    >>> a = ytree.load("tiny_ctrees/locations.dat")
    >>> a = ytree.load("rockstar_halos/trees/tree_0_0_0.dat")
    >>> a = ytree.load("ctrees_hlists/hlists/hlist_0.12521.list")
    >>> # Rockstar catalogs
    >>> a = ytree.load("rockstar_halos/out_0.list")
    >>> # treefarm catalogs
    >>> a = ytree.load("my_halos/fof_subhalo_tab_025.0.h5")
    >>> # LHaloTree catalogs
    >>> a = ytree.load("my_halos/trees_063.0")
    >>> # Amiga Halo Finder
    >>> a = ytree.load("ahf_halos/snap_N64L16_000.parameter",
    ...                hubble_constant=0.7)

    """
    if isinstance(filename, (list, tuple)):
        for fn in filename:
            if not os.path.exists(fn):
                raise IOError("file does not exist: %s." % fn)
    elif not os.path.exists(filename):
        raise IOError("file does not exist: %s." % filename)

    if method is None:
        candidates = []
        for candidate, c in arbor_registry.items():
            try:
                if c._is_valid(filename, **kwargs):
                    candidates.append(candidate)
            except BaseException:
                pass

        if len(candidates) == 0:
            raise IOError("Could not determine arbor type for %s." % filename)
        elif len(candidates) > 1:
            errmsg = "Could not distinguish between these arbor types:\n"
            for candidate in candidates:
                errmsg += "Possible: %s.\n" % candidate
            errmsg += "Provide one of these types using the \'method\' keyword."
            raise IOError(errmsg)
        else:
            method = candidates[0]

    else:
        if method not in arbor_registry:
            raise IOError("Invalid method: %s.  Available: %s." %
                          (method, arbor_registry.keys()))

    global load_warn
    if method not in ["YTree", "LHaloTree", "ConsistentTreeHDF5"] and load_warn:
        print(
            ("Performance will be improved by saving this arbor with " +
             "\"save_arbor\" and reloading:\n" +
             "\t>>> a = ytree.load(\"%s\")\n" +
             "\t>>> fn = a.save_arbor()\n" +
             "\t>>> a = ytree.load(fn)") % filename)
        load_warn = False
    return arbor_registry[method](filename, **kwargs)
