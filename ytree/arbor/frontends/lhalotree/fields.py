"""
LHaloTreeArbor fields



"""

#-----------------------------------------------------------------------------
# Copyright (c) 2017, ytree development team
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

class LHaloTreeFieldInfo(FieldInfoContainer):
    alias_fields = (
        ("uid", "SubhaloIndex", None),
        # ("desc_uid", "desc_uid", None),
        ("scale_factor", "scale_factor", None),
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
        # ("angular_momentum_x", "Jx", None),
        # ("angular_momentum_y", "Jy", None),
        # ("angular_momentum_z", "Jz", None),
        ("spin_parameter", "Spin", None),
    )

    # def setup_derived_fields(self):
    #     """Add derivations that take part of multi-dimensional arrays."""
    #     # Position
    #     def _x(data):
    #         return data['Pos'][:, 0]
    #     def _y(data):
    #         return data['Pos'][:, 1]
    #     def _z(data):
    #         return data['Pos'][:, 2]
    #     pos_unit = self.arbor._lhtreader.units_len
    #     for n, f in zip(['x', 'y', 'z'], [_x, _y, _z]):
    #         self.arbor.add_derived_field(
    #             "position_" + n, f, units=pos_unit, force_add=False)
    #     # Velocity
    #     def _vx(data):
    #         return data['Vel'][:, 0]
    #     def _vy(data):
    #         return data['Vel'][:, 1]
    #     def _vz(data):
    #         return data['Vel'][:, 2]
    #     vel_unit = self.arbor._lhtreader.units_vel
    #     for n, f in zip(['x', 'y', 'z'], [_vx, _vy, _vz]):
    #         self.arbor.add_derived_field(
    #             "velocity_" + n, f, units=pos_unit, force_add=False)

