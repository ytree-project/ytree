"""
ytree exceptions



"""

#-----------------------------------------------------------------------------
# Copyright (c) 2017, Britton Smith <brittonsmith@gmail.com>
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

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
        return ("Field dependency not found: \"%s\" " + \
                "(dependency for \"%s\") in %s.") % \
                (self.dependency, self.field, self.arbor)

class ArborFieldCircularDependency(ArborFieldException):
    def __str__(self):
        return "Field depends on itself: \"%s\" in %s." % \
          (self.field, self.arbor)

class ArborFieldNotFound(ArborFieldException):
    def __str__(self):
        return "Field not found: \"%s\" in %s." % \
          (self.field, self.arbor)
