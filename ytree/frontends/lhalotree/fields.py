"""
LHaloTreeArbor fields



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

# This is where we set aliases for LHaloTree field names to univeral
# field names.
# Syntax is: (<universal field name>, <field name on disk>, <units>)
# TODO: Use units from parameter file

class LHaloTreeFieldInfo(FieldInfoContainer):
    alias_fields = (
        # ("uid", "uid", None),
        # ("desc_uid", "desc_uid", None),
        # ("scale_factor", "scale_factor", None),
        ("mass", "Mvir", m_unit),
        ("virial_mass", "Mvir", m_unit),
        # ("virial_radius", "Rvir", r_unit),
        # ("scale_radius", "rs", r_unit),
        ("velocity_dispersion", "VelDisp", v_unit),
        ("position_x", "x", p_unit),
        ("position_y", "y", p_unit),
        ("position_z", "z", p_unit),
        ("velocity_x", "vx", v_unit),
        ("velocity_y", "vy", v_unit),
        ("velocity_z", "vz", v_unit),
        ("angular_momentum_x", "Jx", None),
        ("angular_momentum_y", "Jy", None),
        ("angular_momentum_z", "Jz", None),
        # ("spin_parameter", "Spin", None),
    )
