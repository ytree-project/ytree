"""
ytree exceptions



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

class ArborDataFileEmpty(Exception):
    def __init__(self, filename):
        self.filename = filename

    def __str__(self):
        return (f"Data file is empty: {self.filename}.")

class ArborFieldException(Exception):
    def __init__(self, field, arbor=None):
        self.field = field
        self.arbor = arbor

class ArborFieldDependencyNotFound(Exception):
    def __init__(self, field, dependency, arbor=None):
        self.field = field
        self.dependency = dependency
        self.arbor = arbor

    def __str__(self):
        return ("Field dependency not found: \"%s\" "
                "(dependency for \"%s\") in %s.") % \
            (self.dependency, self.field, self.arbor)

class ArborFieldCircularDependency(ArborFieldException):
    def __str__(self):
        return f"Field depends on itself: \"{self.field}\" in {self.arbor}."

class ArborFieldNotFound(ArborFieldException):
    def __str__(self):
        return f"Field not found: \"{self.field}\" in {self.arbor}."

class ArborFieldAlreadyExists(ArborFieldException):
    def __str__(self):
        return f"Field already exists: \"{self.field}\" in {self.arbor}."

class ArborAnalysisFieldNotGenerated(ArborFieldException):
    def __str__(self):
        return ("Analysis field \"%s\" needed but "
                "not yet generated in %s.") % \
          (self.field, self.arbor)

class ArborAnalysisFieldNotFound(ArborFieldException):
    def __str__(self):
        return ("Analysis field \"%s\" has been removed "
                "from arbor field storage in %s.") % \
          (self.field, self.arbor)

class ArborUnsettableField(ArborFieldException):
    def __str__(self):
        return ("Cannot set values for field \"%s\" in %s. "
                "Only analysis fields can be set.") % \
          (self.field, self.arbor)
