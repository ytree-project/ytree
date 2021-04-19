"""
ytree-specific fields




"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree Development Team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

from yt.fields.field_info_container import \
    FieldInfoContainer

p_units = 'unitary'
v_units = 'km/s'

def _redshift(field, data):
    ptype, _ = field.name
    return 1. / data[ptype, 'scale_factor'] - 1

def _time(field, data):
    ptype, _ = field.name
    return data.ds.cosmology.t_from_z(data[ptype, "redshift"])

class YTreeFieldInfo(FieldInfoContainer):
    known_other_fields = (
    )

    known_particle_fields = (
        ("position_x", (p_units, ('halos', 'particle_position_x'), None)),
        ("position_y", (p_units, ('halos', 'particle_position_y'), None)),
        ("position_z", (p_units, ('halos', 'particle_position_z'), None)),
        ("velocity_x", (v_units, ('halos', 'particle_velocity_x'), None)),
        ("velocity_y", (v_units, ('halos', 'particle_velocity_y'), None)),
        ("velocity_z", (v_units, ('halos', 'particle_velocity_z'), None)),
        ("mass", ('Msun', ('halos', 'particle_mass'), None)),
    )

    def setup_particle_fields(self, ptype):
        if (ptype, "redshift") not in self.ds.field_list:
            self.add_field((ptype, 'redshift'), function=_redshift,
                           sampling_type='particle', units='')

        if (ptype, "time") not in self.ds.field_list:
            self.add_field((ptype, 'time'), function=_time,
                           sampling_type='particle', units='Gyr')

        super().setup_particle_fields(ptype)
