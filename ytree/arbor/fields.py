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

from collections import \
    defaultdict
import numpy as np
import weakref

from ytree.utilities.exceptions import \
    ArborFieldCircularDependency, \
    ArborFieldDependencyNotFound, \
    ArborFieldNotFound

class FieldInfoContainer(dict):
    """
    A container for information about fields.
    """

    alias_fields = ()
    known_fields = ()
    vector_fields = ("position", "velocity", "angular_momentum")

    def __init__(self, arbor):
        self.arbor = weakref.proxy(arbor)

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

    def setup_derived_fields(self):
        """
        Add stock derived fields.
        """
        def _redshift(field, data):
            return 1. / data["scale_factor"] - 1.
        self.arbor.add_derived_field(
            "redshift", _redshift, units="", force_add=False)

    def setup_vector_fields(self):
        """
        Add vector and magnitude fields.
        """

        def _vector_func(field, data):
            name = field["name"]
            field_data = data.arbor.arr([data["%s_%s" % (name, ax)]
                                         for ax in axes])
            field_data = np.rollaxis(field_data, 1)
            return field_data

        def _magnitude_func(field, data):
            name = field["name"][:-len("_magnitude")]
            return np.sqrt((data[name]**2).sum(axis=1))

        axes = "xyz"
        added_fields = []
        for field in self.vector_fields:
            exists = all([("%s_%s" % (field, ax)) in self for ax in axes])
            if not exists:
                continue

            units = self["%s_x" % field].get("units", None)
            self.arbor.add_derived_field(
                field, _vector_func, vector_field=True, units=units)
            self.arbor.add_derived_field(
                "%s_magnitude" % field, _magnitude_func, units=units)
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
                if fsize is None or fcache[field].size == fsize:
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

class FakeFieldContainer(defaultdict):
    """
    A fake field data container used to calculate dependencies.
    """
    def __init__(self, arbor, name=None):
        self.arbor = weakref.proxy(arbor)
        self.name = name

    def __missing__(self, key):
        if key not in self.arbor.field_info:
            raise ArborFieldDependencyNotFound(
                self.name, key, self.arbor)
        fi = self.arbor.field_info[key]
        units = fi.get("units", "")
        if fi.get("vector_field", False):
            data = np.ones((1, 3))
        else:
            data = np.ones(1)
        self[key] = self.arbor.arr(data, units)
        return self[key]
