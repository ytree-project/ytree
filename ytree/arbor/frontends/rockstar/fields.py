"""
RockstarArbor fields



"""

#-----------------------------------------------------------------------------
# Copyright (c) 2017, Britton Smith <brittonsmith@gmail.com>
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

from ytree.arbor.frontends.rockstar.misc import \
    Group

def setup_field_groups():
    m = Group("masses")
    m.add_thing(lambda a: a.lower().startswith("m"))
    p = Group("positions")
    p.add_thing(lambda a: a.lower() in list("xyz"))
    v = Group("velocities")
    v.add_thing(lambda a: a.lower().startswith("v"))
    r = Group("radii")
    r.add_thing(lambda a: a.lower().startswith("r"))
    r.add_thing(lambda a: (len(a) > 1 and a.lower().startswith("x")))
    a = Group("angular")
    a.add_thing(lambda a: a.lower().startswith("j"))
    return [m, p, v, r, a]
