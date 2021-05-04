"""
MoriaArbor fields



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

a_unit = "Msun/h/yr"
m_unit = "Msun/h"
p_unit = "Mpc/h"
r_unit = "kpc/h"
v_unit = "km/s"
j_unit = "Msun * Mpc * km * s**-1 * h**-2"

def _arbor_index_field(field, data):
    vals = getattr(data.arbor, f"_{field['name']}s")
    return vals[data["snap_index"].astype(int)]

class MoriaFieldInfo(FieldInfoContainer):
    alias_fields = (
        ("position_x", "x_0", p_unit),
        ("position_y", "x_1", p_unit),
        ("position_z", "x_2", p_unit),
        ("velocity_x", "v_0", v_unit),
        ("velocity_y", "v_1", v_unit),
        ("velocity_z", "v_2", v_unit),
        ("angular_momentum_x", "Jx", j_unit),
        ("angular_momentum_y", "Jy", j_unit),
        ("angular_momentum_z", "Jz", j_unit),
        ("velocity_dispersion", "vrms", v_unit),
        ("uid", "id", ""),
        ("desc_uid", "descendant_id", ""),
    )

    known_fields = (
        ("A[x]", r_unit),
        ("A[x](500c)", r_unit),
        ("A[y]", r_unit),
        ("A[y](500c)", r_unit),
        ("A[z]", r_unit),
        ("A[z](500c)", r_unit),
        ("Acc_Rate_1*Tdyn", a_unit),
        ("Acc_Rate_100Myr", a_unit),
        ("Acc_Rate_2*Tdyn", a_unit),
        ("Acc_Rate_Inst", a_unit),
        ("Acc_Rate_Mpeak", a_unit),
        ("First_Acc_Mvir", m_unit),
        ("First_Acc_Vmax", v_unit),
        ("Halfmass_Radius", r_unit),
        ("Jx", j_unit),
        ("Jy", j_unit),
        ("Jz", j_unit),
        ("M200c_all_spa", m_unit),
        ("M200c_bnd_cat", m_unit),
        ("M200c_tcr_spa", m_unit),
        ("M200m_all_spa", m_unit),
        ("M200m_all_spa_internal", m_unit),
        ("M200m_bnd_cat", m_unit),
        ("M200m_peak_cat", m_unit),
        ("M200m_tcr_spa", m_unit),
        ("M500c_all_spa", m_unit),
        ("M500c_bnd_cat", m_unit),
        ("M500c_tcr_spa", m_unit),
        ("Macc", m_unit),
        ("Mpeak", m_unit),
        ("Msp-apr-mn", m_unit),
        ("Msp-apr-p50", m_unit),
        ("Msp-apr-p70", m_unit),
        ("Msp-apr-p75", m_unit),
        ("Msp-apr-p80", m_unit),
        ("Msp-apr-p85", m_unit),
        ("Msp-apr-p90", m_unit),
        ("Mvir_all_spa", m_unit),
        ("Mvir_bnd_cat", m_unit),
        ("Mvir_tcr_spa", m_unit),
        ("R200c_all_spa", r_unit),
        ("R200c_bnd_cat", r_unit),
        ("R200c_tcr_spa", r_unit),
        ("R200m_all_spa", r_unit),
        ("R200m_all_spa_internal", r_unit),
        ("R200m_bnd_cat", r_unit),
        ("R200m_tcr_spa", r_unit),
        ("R500c_all_spa", r_unit),
        ("R500c_bnd_cat", r_unit),
        ("R500c_tcr_spa", r_unit),
        ("Rs_Klypin", r_unit),
        ("Rsp-apr-mn", r_unit),
        ("Rsp-apr-p50", r_unit),
        ("Rsp-apr-p70", r_unit),
        ("Rsp-apr-p75", r_unit),
        ("Rsp-apr-p80", r_unit),
        ("Rsp-apr-p85", r_unit),
        ("Rsp-apr-p90", r_unit),
        ("Rvir_all_spa", r_unit),
        ("Rvir_bnd_cat", r_unit),
        ("Rvir_tcr_spa", r_unit),
        ("Time_to_future_merger", "Gyr"),
        ("Vacc", v_unit),
        ("Vmax@Mpeak", v_unit),
        ("Voff", v_unit),
        ("Vpeak", v_unit),
        ("Xoff", r_unit),
        ("rs", r_unit),
        ("v", v_unit),
        ("vmax", v_unit),
        ("vrms", v_unit),
        ("x", p_unit),
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
            "redshift", _arbor_index_field,
            units="", force_add=False)
        # this will add it to field list for saving
        self.arbor.field_list.append("redshift")

        self.arbor.add_derived_field(
            "scale_factor", _arbor_index_field,
            units="", force_add=False)
        # this will add it to field list for saving
        self.arbor.field_list.append("scale_factor")

        self.arbor.add_derived_field(
            "time", _arbor_index_field,
            units="Gyr", force_add=False)
        # this will add it to field list for saving
        self.arbor.field_list.append("time")

        super().setup_derived_fields()
