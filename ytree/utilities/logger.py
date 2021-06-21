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
    f = logging.Formatter(f"P{comm.rank:03d} {ufstring}")
    if len(ytreeLogger.handlers) > 0:
        ytreeLogger.handlers[0].setFormatter(f)

class fake_pbar:
    def __init__(self, *args):
        pass
    def update(self, *args):
        pass
    def finish(self):
        pass

class log_level():
    """
    Context manager for setting log level.
    """
    def __init__(self, minlevel, mylog=None):
        if mylog is None:
            mylog = ytreeLogger
        self.mylog = mylog
        self.minlevel = minlevel
        self.level = mylog.level

    def __enter__(self):
        if self.level > 10 and self.level < self.minlevel:
            self.mylog.setLevel(40)

    def __exit__(self, *args):
        self.mylog.setLevel(self.level)
