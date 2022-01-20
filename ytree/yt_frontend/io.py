"""
ytree io




"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree Development Team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import h5py
from more_itertools import always_iterable
import numpy as np
from packaging import version
from pkg_resources import get_distribution

from yt.utilities.io_handler import BaseIOHandler

_ptype = "halos"

need_hsml = version.parse(get_distribution("yt").version) >= \
  version.parse("4.1.dev0")

class IOHandlerYTreeHDF5(BaseIOHandler):
    _dataset_type = "ytree_arbor"

    def _read_fluid_selection(self, chunks, selector, fields, size):
        raise NotImplementedError

    def _read_particle_coords(self, chunks, ptf):
        for data_file in self._yield_data_files(chunks):
            x, y, z = data_file._get_particle_positions(_ptype)
            if need_hsml:
                yield _ptype, (x, y, z), 0.0
            else:
                yield _ptype, (x, y, z)

    def _read_particle_fields(self, chunks, ptf, selector):
        for data_file in self._yield_data_files(chunks):
            with h5py.File(data_file.filename, "r") as f:
                for ptype, field_list in sorted(ptf.items()):
                    x, y, z = data_file._get_particle_positions(ptype, f=f)
                    mask = selector.select_points(x, y, z, 0.0)
                    del x, y, z
                    if mask is None:
                        continue
                    if mask.all():
                        mask = slice(None)
                    for field in field_list:
                        data = data_file._read_field_data(field, mask, f=f)
                        yield (ptype, field), data

    def _yield_data_files(self, chunks):
        chunks = always_iterable(chunks)
        data_files = set([])
        for chunk in chunks:
            for obj in chunk.objs:
                data_files.update(obj.data_files)

        for data_file in sorted(data_files):
            yield data_file

    def _yield_coordinates(self, data_file):
        pos = data_file._get_particle_positions(_ptype, transpose=False)
        pos.convert_to_units("code_length")
        yield _ptype, pos

    def _count_particles(self, data_file):
        si, ei = data_file.start, data_file.end
        if None not in (si, ei):
            pcount = {}
            for ptype, npart in data_file.total_particles_file.items():
                pcount[ptype] = np.clip(npart - si, 0, ei - si)
        else:
            pcount = data_file.total_particles_file
        return pcount

    def _identify_fields(self, data_file):
        _node_fields = ["file_root_index", "file_number", "tree_index"]
        fields = [(_ptype, field) for field in list(self.ds._field_dict.keys()) +
                  _node_fields]
        units = dict(((_ptype, field), self.ds._field_dict[field].get("units", ""))
                     for field in self.ds._field_dict)
        return fields, units
