"""
NodeLink class



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

class NodeLink:
    __slots__ = ('tree_id', 'descendent', 'ancestors')

    def __init__(self, tree_id):
        self.tree_id = tree_id
        self.descendent = None
        self.ancestors = []

    def add_ancestor(self, node):
        self.ancestors.append(node)
        node.descendent = self
