"""
ConsistentTreesArbor fields



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

class ConsistentTreesFieldInfo(FieldInfoContainer):
    alias_fields = (
        ("uid", "id", None),
        ("desc_uid", "desc_id", None),
        ("halo_id", "Orig_halo_ID", None),
        ("scale_factor", "scale", None),
        ("mass", "Mvir", m_unit),
        ("virial_mass", "Mvir", m_unit),
        ("virial_radius", "Rvir", r_unit),
        ("scale_radius", "rs", r_unit),
        ("velocity_dispersion", "vrms", v_unit),
        ("position_x", "x", p_unit),
        ("position_y", "y", p_unit),
        ("position_z", "z", p_unit),
        ("velocity_x", "vx", v_unit),
        ("velocity_y", "vy", v_unit),
        ("velocity_z", "vz", v_unit),
        ("angular_momentum_x", "Jx", None),
        ("angular_momentum_y", "Jy", None),
        ("angular_momentum_z", "Jz", None),
        ("spin_parameter", "Spin", None),
    )

    data_types = (
        ("id", id_type),
        ("desc_id", id_type),
        ("num_prog", np.int32),
        ("pid", id_type),
        ("upid", id_type),
        ("desc_pid", id_type),
        ("Breadth_first_ID", id_type),
        ("Depth_first_ID", id_type),
        ("Tree_root_ID", id_type),
        ("Orig_halo_ID", id_type),
        ("Snap_idx", id_type),
        ("Next_coprogenitor_depthfirst_ID", id_type),
        ("Last_progenitor_depthfirst_ID", id_type),
        ("Last_mainleaf_depthfirst_ID", id_type),
        ("Tidal_ID", id_type),
    )
