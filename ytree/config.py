"""
ytree config



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import configparser
import os

CONFIG_DIR = os.environ.get("XDG_CONFIG_HOME",
    os.path.join(os.path.expanduser("~"), ".config", "ytree"))

ytreecfg = configparser.ConfigParser()
ytreecfg.read(os.path.join(CONFIG_DIR, "ytreerc"))
if not ytreecfg.has_section("ytree"):
    ytreecfg.add_section("ytree")
