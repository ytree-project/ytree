"""
testing utilities



"""

#-----------------------------------------------------------------------------
# Copyright (c) 2016, Britton Smith <brittonsmith@gmail.com>
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import os
import shutil
import tempfile

def not_on_drone(func, *args, **kwargs):
    """
    Do not run the function if environment variable DRONE=1.
    """

    env = dict(os.environ)
    def myfunc():
        if int(env.get("DRONE", 0)) == 1:
            return
        return func(*args, **kwargs)
    return myfunc

def in_tmpdir(func, *args, **kwargs):
    """
    Make a temp dir, cd into it, run operation,
    return to original location, remove temp dir.
    """

    def do_in_tmpdir(*args, **kwargs):
        tmpdir = tempfile.mkdtemp()
        curdir = os.getcwd()
        os.chdir(tmpdir)
        func(*args, **kwargs)
        os.chdir(curdir)
        shutil.rmtree(tmpdir)

    return do_in_tmpdir

def compare_arbors(a1, a2):
    """
    Compare all fields for all trees in two arbors.
    """

    for t1, t2 in zip(a1.trees, a2.trees):
        for field in a1._field_data:
            assert (t1.tree(field) == t2.tree(field)).all()
