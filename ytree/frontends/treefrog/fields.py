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
        ("uid", "ID", ""),
        ("desc_uid", "Descendant", ""),
        ("velocity_dispersion", "sigV", v_unit),
        ("position_x", "Xc", p_unit),
        ("position_y", "Yc", p_unit),
        ("position_z", "Zc", p_unit),
        ("velocity_x", "VXc", v_unit),
        ("velocity_y", "VYc", v_unit),
        ("velocity_z", "VZc", v_unit),
        ("angular_momentum_x", "Lx", None),
        ("angular_momentum_y", "Ly", None),
        ("angular_momentum_z", "Lz", None),
        ("spin_parameter", "lambda_B", None),
    )

    known_fields = (
        ("Lx", "angular_momentum_unit"),
        ("Ly", "angular_momentum_unit"),
        ("Lz", "angular_momentum_unit"),
        ("Mass_200crit", "mass_unit"),
        ("Mass_200mean", "mass_unit"),
        ("Mass_FOF", "mass_unit"),
        ("Mass_tot", "mass_unit"),
        ("RVmax_Lx", "length_unit"),
        ("RVmax_Ly", "length_unit"),
        ("RVmax_Lz", "length_unit"),
        ("RVmax_sigV", "length_unit"),
        ("R_200crit", "length_unit"),
        ("R_200mean", "length_unit"),
        ("R_HalfMass", "length_unit"),
        ("R_size", "length_unit"),
        ("Rmax", "length_unit"),
        ("VXc", "velocity_unit"),
        ("VYc", "velocity_unit"),
        ("VZc", "velocity_unit"),
        ("Vmax", "velocity_unit"),
        ("Xc", "length_unit"),
        ("Xcminpot", "length_unit"),
        ("Yc", "length_unit"),
        ("Ycminpot", "length_unit"),
        ("Zc", "length_unit"),
        ("Zcminpot", "length_unit"),
        ("sigV", "velocity_unit"),
    )

    data_types = (
        ("ID", id_type),
        ("Descendant", id_type),
    )

    def __init__(self, arbor):
        super().__init__(arbor)
        self._setup_field_units()

    def _setup_field_units(self):
        a = self.arbor
        units = {}
        units["length_unit"] = a.quan(a.units["Length_unit_to_kpc"], "kpc")
        units["mass_unit"] = a.quan(a.units["Mass_unit_to_solarmass"], "Msun")
        units["velocity_unit"] = a.quan(a.units["Velocity_unit_to_kms"], "km/s")
        units["angular_momentum_unit"] = units["mass_unit"] * \
          units["length_unit"] * units["velocity_unit"]

        for unit, val in units.items():
            units[unit] = f"{str(val.d)}*{str(val.units)}"

        known_fields = []
        for field, ustr in self.known_fields:
            known_fields.append((field, units.get(ustr, "")))
        self.known_fields = tuple(known_fields)
