"""
miscellaneous Arbor functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import os

from yt.funcs import \
    ensure_dir

def _determine_output_filename(path, suffix):
    if path.endswith(suffix):
        dirname = os.path.dirname(path)
        filename = path[:-len(suffix)]
    else:
        dirname = path
        filename = os.path.join(
            dirname, os.path.basename(path))
    ensure_dir(dirname)
    return filename
