"""
miscellaneous utilities



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import numpy as np

def fround(val, decimals=0):
    """
    Round 0.5 up to 1 and so on.
    """
    fac = 10**decimals
    return np.floor(val * fac + 0.5) / fac
