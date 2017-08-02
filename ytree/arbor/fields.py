"""
Arbor field-related classes



"""

#-----------------------------------------------------------------------------
# Copyright (c) 2017, Britton Smith <brittonsmith@gmail.com>
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

from collections import \
    defaultdict
import numpy as np

from ytree.utilities.exceptions import \
    ArborFieldCircularDependency, \
    ArborFieldDependencyNotFound, \
    ArborFieldNotFound

class FieldInfoContainer(dict):
    """
    A container for information about fields.
    """

    alias_fields = ()
    def __init__(self, arbor):
        self.arbor = arbor

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
        def _redshift(data):
            return 1. / data["scale_factor"] - 1.
        self.arbor.add_derived_field(
            "redshift", _redshift, units="", force_add=False)

    def resolve_field_dependencies(self, fields, fcache=None):
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
                continue
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
        self.arbor = arbor

class FakeFieldContainer(defaultdict):
    """
    A fake field data container used to calculate dependencies.
    """
    def __init__(self, arbor, name=None):
        self.arbor = arbor
        self.name = name

    def __missing__(self, key):
        if key not in self.arbor.field_info:
            raise ArborFieldDependencyNotFound(
                self.name, key, self.arbor)
        units = self.arbor.field_info[key].get("units", "")
        self[key] = self.arbor.arr(np.ones(1), units)
        return self[key]
