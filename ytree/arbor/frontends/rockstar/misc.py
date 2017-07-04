"""
RockstarArbor miscellany



"""

#-----------------------------------------------------------------------------
# Copyright (c) 2017, Britton Smith <brittonsmith@gmail.com>
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import numpy as np

class Group(object):
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

def f_text_block(f, block_size=32768, file_size=None, sep="\n"):
    """
    Read lines from a file faster than f.readlines().
    """
    start = f.tell()
    if file_size is None:
        f.seek(0, 2)
        file_size = f.tell() - start
        f.seek(start)

    nblocks = np.ceil(float(file_size) /
                      block_size).astype(np.int64)
    read_size = file_size + start
    lbuff = ""
    for ib in range(nblocks):
        offset = f.tell()
        my_block = min(block_size, read_size-offset)
        if my_block <= 0: break
        buff = f.read(my_block)
        linl = -1
        for ih in range(buff.count(sep)):
            inl = buff.find(sep, linl+1)
            if inl < 0:
                lbuff += buff[linl+1:]
                continue
            else:
                line = lbuff + buff[linl+1:inl]
                loc = offset - len(lbuff) + linl + 1
                lbuff = ""
                linl = inl
                yield line, loc
        lbuff += buff[linl+1:]
    if lbuff:
        loc = f.tell() - len(lbuff)
        yield lbuff, loc
