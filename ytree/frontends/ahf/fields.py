"""
AHFArbor fields



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

m_unit = "Msun/h"
p_unit = "kpc/h"
v_unit = "km/s"

id_type = np.int64

class AHFFieldInfo(FieldInfoContainer):
    known_fields = (
        ("Mvir", m_unit),
        ("Xc", p_unit),
        ("Yc", p_unit),
        ("Zc", p_unit),
        ("VXc", v_unit),
        ("VYc", v_unit),
        ("VZc", v_unit),
        ("Rvir", p_unit),
        ("Rmax", p_unit),
        ("r2", p_unit),
        ("mbp_offset", p_unit),
        ("com_offset", p_unit),
        ("Vmax", v_unit),
        ("v_esc", v_unit),
        ("sigV", v_unit),
        ("Ekin", "Msun/h * (km/s)**2"),
        ("Epot", "Msun/h * (km/s)**2"),
        ("SurfP", "Msun/h * (km/s)**2"),
        ("Phi0", "(km/s)**2"),
    )

    alias_fields = (
        ("halo_id", "ID", None),
        ("mass", "Mvir", m_unit),
        ("virial_mass", "Mvir", m_unit),
        ("position_x", "Xc", p_unit),
        ("position_y", "Yc", p_unit),
        ("position_z", "Zc", p_unit),
        ("velocity_x", "VXc", v_unit),
        ("velocity_y", "VYc", v_unit),
        ("velocity_z", "VZc", v_unit),
        ("virial_radius", "Rvir", p_unit),
        ("velocity_dispersion", "sigV", v_unit),
        ("spin_parameter", "lambda", None),
        ("kinetic_energy", "Ekin", "Msun/h * (km/s)**2"),
        ("potential_energy", "Epot", "Msun/h * (km/s)**2"),
    )

    data_types = (
        ('ID', id_type),
        ('desc_id', id_type),
        ('uid', id_type),
        ('desc_uid', id_type)
    )
