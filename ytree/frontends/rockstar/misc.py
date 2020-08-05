"""
RockstarArbor miscellany



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

class Group:
    def __init__(self, name=None):
        self.things = None
        if name is not None:
            self.add_thing(
                lambda a: name.lower() in a.lower())
        self.name = name
    def add_thing(self, thing):
        if self.things is None:
            self.things = []
        self.things.append(thing)
    def in_group(self, item):
        if self.things is None:
            return False
        for thing in self.things:
            try:
                if thing(item):
                    return True
            except Exception:
                continue
        return False
