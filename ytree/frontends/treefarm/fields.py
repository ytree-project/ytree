"""
TreeFarmArbor fields



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

from ytree.data_structures.fields import \
    FieldInfoContainer

m_unit = "Msun"
p_unit = "unitary"
r_unit = "kpc"
v_unit = "km/s"

class TreeFarmFieldInfo(FieldInfoContainer):
    alias_fields = (
        ("halo_id", "particle_identifier", None),
        ("desc_id", "descendent_identifier", None),
        ("mass", "particle_mass", m_unit),
        ("position_x", "particle_position_x", p_unit),
        ("position_y", "particle_position_y", p_unit),
        ("position_z", "particle_position_z", p_unit),
        ("velocity_x", "particle_velocity_x", v_unit),
        ("velocity_y", "particle_velocity_y", v_unit),
        ("velocity_z", "particle_velocity_z", v_unit),
    )
