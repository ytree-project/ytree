"""
loading utilities



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import os

from ytree.config import \
    ytreecfg

if "YTREE_TEST_DATA_DIR" in os.environ:
    test_data_dir = os.environ["YTREE_TEST_DATA_DIR"]
else:
    test_data_dir = ytreecfg["ytree"].get("test_data_dir", ".")

def check_path(filename):
    """
    Check file exists in place or in test data dir.
    """

    if os.path.exists(filename):
        return filename
    tfn = os.path.join(test_data_dir, filename)
    if os.path.exists(tfn):
        return tfn
    raise IOError(f"File does not exist: {filename}.")

def get_path(filename):
    """
    Get a path or list of paths.
    """

    if isinstance(filename, (list, tuple)):
        path = [check_path(fn) for fn in filename]
    else:
        path = check_path(filename)
    return path
