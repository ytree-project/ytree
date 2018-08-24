"""
ytree logger



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import logging
import sys

# CRITICAL 50
# ERROR    40
# WARNING  30
# INFO     20
# DEBUG    10
# NOTSET   10

ufstring = "%(name)-3s: [%(levelname)-9s] %(asctime)s %(message)s"

ytreeLogger = logging.getLogger("ytree")
ytree_sh = logging.StreamHandler(stream=sys.stderr)
formatter = logging.Formatter(ufstring)
ytree_sh.setFormatter(formatter)
ytreeLogger.addHandler(ytree_sh)
ytreeLogger.setLevel(20)
ytreeLogger.propagate = False

def set_parallel_logger(comm):
    if comm.size == 1: return
    f = logging.Formatter("P%03i %s" % (comm.rank, ufstring))
    if len(ytreeLogger.handlers) > 0:
        ytreeLogger.handlers[0].setFormatter(f)

class fake_pbar(object):
    def __init__(self, *args):
        pass
    def update(self, *args):
        pass
    def finish(self):
        pass
