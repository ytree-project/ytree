"""
RockstarArbor fields



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
from ytree.arbor.frontends.rockstar.misc import \
    Group

m_unit = "Msun"
p_unit = "unitary"
r_unit = "kpc"
v_unit = "km/s"

class RockstarFieldInfo(FieldInfoContainer):
    alias_fields = (
        ("halo_id", "ID", None),
        ("desc_id", "DescID", None),
        ("mass", "Mvir", m_unit),
        ("virial_mass", "Mvir", m_unit),
        ("virial_radius", "Rvir", r_unit),
        ("scale_radius", "Rs", r_unit),
        ("velocity_dispersion", "Vrms", v_unit),
        ("position_x", "X", p_unit),
        ("position_y", "Y", p_unit),
        ("position_z", "Z", p_unit),
        ("velocity_x", "VX", v_unit),
        ("velocity_y", "VY", v_unit),
        ("velocity_z", "VZ", v_unit),
        ("angular_momentum_x", "JX", None),
        ("angular_momentum_y", "JY", None),
        ("angular_momentum_z", "JZ", None),
        ("spin_parameter", "Spin", None),
    )

def setup_field_groups():
    m = Group("masses")
    m.add_thing(lambda a: a.lower().startswith("m"))
    p = Group("positions")
    p.add_thing(lambda a: a.lower() in list("xyz"))
    v = Group("velocities")
    v.add_thing(lambda a: a.lower().startswith("v"))
    r = Group("radii")
    r.add_thing(lambda a: a.lower().startswith("r"))
    r.add_thing(lambda a: (len(a) > 1 and a.lower().startswith("x")))
    a = Group("angular")
    a.add_thing(lambda a: a.lower().startswith("j"))
    return [m, p, v, r, a]
