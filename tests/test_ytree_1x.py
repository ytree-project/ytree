"""
tests for backward compatibility with ytree 1.x



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import glob
import h5py
import os
from ytree.utilities.testing import \
    assert_array_rel_equal, \
    compare_hdf5, \
    requires_file, \
    test_data_dir, \
    TempDirTest

import ytree

ytree_1x_data = os.path.join(test_data_dir, "ytree_1x")

def generate_results_file(a, fn, fields):
    fh = h5py.File(fn, "w")
    for t in a:
        tgroup = fh.create_group("group_%d" % t.uid)
        groups = ["prog", "tree"]
        groupnames = ["line", "tree"]
        for gtype, gname in zip(groups, groupnames):
            for field in fields:
                data = t[gtype, field]
                if hasattr(data, "units"):
                    data = data.in_cgs()
                tgroup.create_dataset("%s_%s" % (gname, field),
                                      data=data)
    fh.close()

class YTree1xTest(TempDirTest):
    @requires_file(ytree_1x_data)
    def test_1x_arbors(self):
        results_filenames = \
          glob.glob(os.path.join(test_data_dir,
                                 "ytree_1x/results/*.h5"))

        fields = ["uid", "redshift"]
        for filename in results_filenames:
            basename = os.path.basename(filename)
            arbor_filename = \
              os.path.join(test_data_dir, "ytree_1x/arbors",
                           "arbor_%s" % basename)
            if "tree_farm" in filename:
                tfields = fields + ["particle_mass"]
            else:
                tfields = fields + ["mvir"]

            a = ytree.load(arbor_filename)
            generate_results_file(a, basename, tfields)
            compare_hdf5(basename, filename,
                         compare=assert_array_rel_equal,
                         decimals=15)

    @requires_file(ytree_1x_data)
    def test_1x_tree_farms(self):
        tree_farm_filenames = \
          glob.glob(os.path.join(test_data_dir,
                                 "ytree_1x/arbors/tree_farm*"))

        fields = ["redshift", "particle_mass"]
        for filename in tree_farm_filenames:
            basename = os.path.basename(filename)
            arbor_glob = \
              os.path.join(test_data_dir, "ytree_1x/arbors",
                           basename, "*.h5")
            arbor_filename = glob.glob(arbor_glob)[0]

            results_filename = \
              os.path.join(test_data_dir, "ytree_1x/results",
                           "%s.h5" % basename)

            a = ytree.load(arbor_filename)
            basename = "%s.h5" % os.path.basename(filename)
            generate_results_file(a, basename, fields)
            compare_hdf5(basename, results_filename,
                         compare_groups=False,
                         compare=assert_array_rel_equal,
                         decimals=15)
