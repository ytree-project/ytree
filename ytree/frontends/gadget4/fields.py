"""
Gadget4Arbor fields



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import re

from ytree.data_structures.fields import \
    FieldInfoContainer

m_unit = "1e10 * Msun/h"
p_unit = "Mpc/h"
v_unit = "km/s"
j_unit = f"{p_unit} * {v_unit}"

def _redshift(field, data):
    isn = data["SnapNum"].astype(int)
    return data.arbor.arr(data.arbor._redshifts[isn], "")

class Gadget4FieldInfo(FieldInfoContainer):
    alias_fields = (
        ("group_mass", "Group_M_Crit200", m_unit),
        ("mass", "SubhaloMass", m_unit),
        ("position_x", "SubhaloPos_0", p_unit),
        ("position_y", "SubhaloPos_1", p_unit),
        ("position_z", "SubhaloPos_2", p_unit),
        ("velocity_x", "SubhaloVel_0", v_unit),
        ("velocity_y", "SubhaloVel_1", v_unit),
        ("velocity_z", "SubhaloVel_2", v_unit),
        ("angular_momentum_x", "SubhaloSpin_0", j_unit),
        ("angular_momentum_y", "SubhaloSpin_1", j_unit),
        ("angular_momentum_z", "SubhaloSpin_2", j_unit),
        ("velocity_dispersion", "SubhaloVelDisp", v_unit),
    )

    known_fields = (
        ("Group_M_Crit200", m_unit),
        ("SubhaloHalfmassRad", p_unit),
        ("SubhaloMass", m_unit),
        ("SubhaloPos", p_unit),
        ("SubhaloSpin", j_unit),
        ("SubhaloVel", v_unit),
        ("SubhaloVelDisp", v_unit),
        ("SubhaloVmax", v_unit),
        ("SubhaloVmaxRad", p_unit),
    )

    def setup_known_fields(self):
        """
        Add units for all <fieldname>_<number> fields as well.
        """

        kfields = dict(self.known_fields)
        freg = re.compile(r"(^.+)_\d+$")
        for field in self:
            if self[field].get("units") is not None:
                continue

            if field in kfields:
                self[field]["units"] = kfields[field]
                continue

            fs = freg.search(field)
            if fs and fs.groups()[0] in kfields:
                self[field]["units"] = kfields[fs.groups()[0]]

    def setup_derived_fields(self):
        self.arbor.add_derived_field(
            "redshift", _redshift, units="", force_add=False)
        # this will add it to field list for saving
        self.arbor.field_list.append("redshift")

        super().setup_derived_fields()
