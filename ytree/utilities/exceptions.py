"""
ytree exceptions



"""

# -----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------


class YTreeDataFileEmpty(Exception):
    def __init__(self, filename):
        self.filename = filename

    def __str__(self):
        return f"Data file is empty: {self.filename}."


class YTreeFieldException(Exception):
    def __init__(self, field, arbor=None):
        self.field = field
        self.arbor = arbor


class YTreeDerivedFieldException(YTreeFieldException):
    def __str__(self):
        return f'Derived field "{self.field}" could not be generated for {self.arbor}.'


class YTreeFieldDependencyNotFound(Exception):
    def __init__(self, field, dependency, arbor=None):
        self.field = field
        self.dependency = dependency
        self.arbor = arbor

    def __str__(self):
        return (
            f'Field dependency not found: "{self.dependency}" '
            f'(dependency for "{self.field}") in {self.arbor}.'
        )


class YTreeFieldCircularDependency(YTreeFieldException):
    def __str__(self):
        return f'Field depends on itself: "{self.field}" in {self.arbor}.'


class YTreeFieldNotFound(YTreeFieldException):
    def __str__(self):
        return f'Field not found: "{self.field}" in {self.arbor}.'


class YTreeFieldAlreadyExists(YTreeFieldException):
    def __str__(self):
        return f'Field already exists: "{self.field}" in {self.arbor}.'


class YTreeAnalysisFieldNotGenerated(YTreeFieldException):
    def __str__(self):
        return (
            f'Analysis field "{self.field}" needed but '
            f"not yet generated in {self.arbor}."
        )


class YTreeAnalysisFieldNotFound(YTreeFieldException):
    def __str__(self):
        return (
            f'Analysis field "{self.field}" has been removed '
            f"from arbor field storage in {self.arbor}."
        )


class YTreeUnsettableField(YTreeFieldException):
    def __str__(self):
        return (
            f'Cannot set values for field "{self.field}" in {self.arbor}. '
            "Only analysis fields can be set."
        )
