"""
TreeFrogArbor fields



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import numpy as np

from ytree.data_structures.fields import \
    FieldInfoContainer

m_unit = "Msun"
p_unit = "unitary"
r_unit = "kpc"
v_unit = "km/s"

id_type = np.int64

class TreeFrogFieldInfo(FieldInfoContainer):
    alias_fields = (
        ("uid", "ID", None),
        ("desc_uid", "Descendant", None),
    )

    data_types = (
        ("uid", id_type),
        ("desc_uid", id_type)
    )
