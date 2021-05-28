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
from rich import progress
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

class CompletionSpeedColumn(progress.ProgressColumn):
    """Renders human readable completion speed."""

    # This was written by Clément Robert for yt.
    # This is based off rich.progress.TransferSpeedColumn

    def render(self, task):
        """Show data transfer speed."""
        speed = task.finished_speed or task.speed
        if speed is None:
            return progress.Text("?", style="progress.data.speed")
        data_speed = int(speed)
        return progress.Text(f"{data_speed} it/s", style="progress.data.speed")

def get_pbar(fake=False):
    if fake:
        return FakeProgressBar()
    else:
        return progress.Progress(
            "[progress.description]{task.description}",
            "[progress.percentage]{task.percentage:>3.0f}%",
            progress.BarColumn(),
            "{task.completed}/{task.total}",
            progress.TimeElapsedColumn(),
            progress.TimeRemainingColumn(),
            CompletionSpeedColumn())

class FakeProgressBar:
    def __init__(self, *args, **kwargs):
        pass
    def add_task(self, *args, **kwargs):
        pass
    def update(self, *args, **kwargs):
        pass
    def __enter__(self, *args, **kwargs):
        return self
    def __exit__(self, *args, **kwargs):
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
