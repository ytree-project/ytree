"""
ArborArborArbor fields



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

from ytree.arbor.fields import \
    FieldInfoContainer

m_unit = "Msun"
p_unit = "unitary"
r_unit = "kpc"
v_unit = "km/s"

class ArborArborFieldInfo(FieldInfoContainer):
    alias_fields = (
        ("id", ("ID", "particle_identifier", "uid"), None),
        ("scale_factor", "scale", None),
        ("mass", ("Mvir", "mvir", "particle_mass"), m_unit),
        ("virial_radius", "Rvir", r_unit),
        ("position_x", ("X", "x", "particle_position_x"), p_unit),
        ("position_y", ("Y", "y", "particle_position_y"), p_unit),
        ("position_z", ("Z", "z", "particle_position_z"), p_unit),
        ("velocity_x", ("VX", "vx", "particle_velocity_x"), v_unit),
        ("velocity_y", ("VY", "vy", "particle_velocity_y"), v_unit),
        ("velocity_z", ("VZ", "vz", "particle_velocity_z"), v_unit),
        ("angular_momentum_x", ("JX", "Jx"), None),
        ("angular_momentum_y", ("JY", "Jy"), None),
        ("angular_momentum_z", ("JZ", "Jz"), None),
        ("spin_parameter", "Spin", None),
    )
