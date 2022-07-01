"""
Arbor field-related classes



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import numpy as np
import weakref

from ytree.data_structures.detection import FieldDetector
from ytree.utilities.exceptions import \
    ArborFieldAlreadyExists, \
    ArborFieldCircularDependency, \
    ArborFieldDependencyNotFound, \
    ArborFieldNotFound
from ytree.utilities.logger import \
    ytreeLogger as mylog

def _redshift(field, data):
    return 1. / data["scale_factor"] - 1.

def _time(field, data):
    return data.arbor.cosmology.t_from_z(data["redshift"])

def _vector_func(field, data):
    name = field["name"]
    field_data = data.arbor.arr([data[f"{name}_{ax}"]
                                 for ax in "xyz"])
    field_data = np.rollaxis(field_data, 1)
    return field_data

def _magnitude_func(field, data):
    name = field["name"][:-len("_magnitude")]
    return np.sqrt((data[name]**2).sum(axis=1))

class FieldInfoContainer(dict):
    """
    A container for information about fields.
    """

    alias_fields = ()
    known_fields = ()
    vector_fields = ("position", "velocity", "angular_momentum")
    data_types = ()

    def __init__(self, arbor):
        self.arbor = weakref.proxy(arbor)
        self._data_types = dict(self.data_types)

    def setup_known_fields(self):
        """
        Add units for fields on disk as defined in the known_fields
        tuple.
        """
        for field, units in self.known_fields:
            if field not in self:
                continue
            funits = self[field].get("units")
            if funits is None:
                self[field]["units"] = units

    def add_analysis_field(self, name, units, dtype=None, default=0):
        """
        Add an analysis field.
        """

        if name in self:
            raise ArborFieldAlreadyExists(name, arbor=self)

        if dtype is None:
            dtype = self.arbor._default_dtype

        self.arbor.analysis_field_list.append(name)
        self[name] = {"type": "analysis",
                      "default": default,
                      "dtype": dtype,
                      "units": units}

    def add_alias_field(self, alias, field, units=None,
                        force_add=True):
        """
        Add an alias field.
        """

        if alias in self:
            if force_add:
                ftype = self[alias].get("type", "on-disk")
                if ftype in ["alias", "derived"]:
                    fl = self.arbor.derived_field_list
                else:
                    fl = self.arbor.field_list
                mylog.warning(
                    f"Overriding field \"{alias}\" that already "
                    f"exists as {ftype} field.")
                fl.pop(fl.index(alias))
            else:
                return

        if field not in self:
            if force_add:
                raise ArborFieldDependencyNotFound(
                    field, alias, arbor=self)
            else:
                return

        if units is None:
            units = self[field].get("units")
        self.arbor.derived_field_list.append(alias)
        self[alias] = \
          {"type": "alias", "units": units,
           "dependencies": [field]}
        if "aliases" not in self[field]:
            self[field]["aliases"] = []
            self[field]["aliases"].append(alias)

    def setup_aliases(self):
        """
        Add aliases defined in the alias_fields tuple for each frontend.
        """
        for alias in self.alias_fields:
            aliasname, fieldname, units = alias
            if not isinstance(fieldname, tuple):
                fieldname = (fieldname,)
            for fname in fieldname:
                self.arbor.add_alias_field(
                    aliasname, fname, units=units,
                    force_add=False)

        # Fields with "/" in the name don't play well with hdf5.
        for field in self.arbor.field_list:
            if "/" not in field:
                continue
            alias = field.replace("/", "_")
            self.arbor.add_alias_field(alias, field)

    def add_derived_field(self, name, function,
                          units=None, dtype=None, description=None,
                          vector_field=False, force_add=True):
        """
        Add a derived field.
        """

        if name in self:
            if force_add:
                ftype = self[name].get("type", "on-disk")
                if ftype in ["alias", "derived"]:
                    fl = self.arbor.derived_field_list
                else:
                    fl = self.arbor.field_list
                mylog.warning(
                    f"Overriding field \"{name}\" that already "
                    f"exists as {ftype} field.")
                fl.pop(fl.index(name))
            else:
                return

        if units is None:
            units = ""
        if dtype is None:
            dtype = self.arbor._default_dtype
        info = {"name": name,
                "type": "derived",
                "function": function,
                "units": units,
                "dtype": dtype,
                "vector_field": vector_field,
                "description": description}

        fc = FieldDetector(self.arbor, name=name)
        try:
            rv = function(info, fc)
        except TypeError as e:
            raise RuntimeError(
"""

Field function syntax in ytree has changed. Field functions must
now take two arguments, as in the following:
def my_field(field, data):
    return data['mass']

Check the TypeError exception above for more details.
""")
            raise e

        except ArborFieldDependencyNotFound as e:
            if force_add:
                raise e
            else:
                return

        rv.convert_to_units(units)
        info["dependencies"] = list(fc.keys())

        self.arbor.derived_field_list.append(name)
        self[name] = info

    def setup_derived_fields(self):
        """
        Add stock derived fields.
        """
        self.arbor.add_derived_field(
            "redshift", _redshift, units="", force_add=False)

        if hasattr(self.arbor, "cosmology"):
            self.arbor.add_derived_field(
                "time", _time, units="Myr", force_add=False)

    def add_vector_field(self, fieldname):
        """
        Add vector and magnitude fields for a field with
        x/y/z components.
        """

        cfields = [f"{fieldname}_{ax}" for ax in "xyz"]
        exists = all([field in self for field in cfields])
        if not exists:
            return None

        for field in cfields:
            self[field]["vector_fieldname"] = fieldname

        units = self[cfields[0]].get("units", None)
        self.arbor.add_derived_field(
            fieldname, _vector_func, vector_field=True, units=units)
        self.arbor.add_derived_field(
            f"{fieldname}_magnitude", _magnitude_func, units=units)
        return fieldname

    def setup_vector_fields(self):
        """
        Add vector and magnitude fields.
        """

        added_fields = []
        for field in self.vector_fields:
            field = self.add_vector_field(field)
            if field is None:
                continue
            added_fields.append(field)

        self.vector_fields = tuple(added_fields)

    def resolve_field_dependencies(self, fields, fcache=None, fsize=None):
        """
        Divide fields into those to be read and those to generate.
        """
        if fcache is None:
            fcache = {}
        fields_to_read = []
        fields_to_generate = []
        fields_to_resolve = fields[:]

        while len(fields_to_resolve) > 0:
            field = fields_to_resolve.pop(0)
            if field in fcache:
                # Check that the field array is the size we want.
                # It might not be if it was previously gotten just
                # for the root and now we want it for the whole tree.
                if fsize is None or fcache[field].shape[0] == fsize:
                    continue
                del fcache[field]

            if field not in self:
                raise ArborFieldNotFound(field, self.arbor)

            ftype = self[field].get("type")
            if ftype == "derived" or ftype == "alias":
                deps = self[field]["dependencies"]
                if field in deps:
                    raise ArborFieldCircularDependency(
                        field, self.arbor)
                fields_to_resolve.extend(
                    set(deps).difference(set(fields_to_resolve)))
                if field not in fields_to_generate:
                    fields_to_generate.append(field)
            elif ftype == "analysis":
                fields_to_generate.append(field)
            else:
                if field not in fields_to_read:
                    fields_to_read.append(field)

        return fields_to_read, fields_to_generate

class FieldContainer(dict):
    """
    A container for field data.
    """
    def __init__(self, arbor):
        self.arbor = weakref.proxy(arbor)
