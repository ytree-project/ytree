.. _api-reference:

API Reference
=============

Working with Merger-Trees
-------------------------

The :func:`~ytree.arbor.arbor.load` can load all supported
merger-tree formats.  Once loaded, the
:func:`~ytree.arbor.arbor.Arbor.save_arbor` and
:func:`~ytree.arbor.tree_node.TreeNode.save_tree` functions can be
used to save the entire arbor or individual trees.

.. autosummary::
   :toctree: generated/

   ~ytree.arbor.arbor.load
   ~ytree.arbor.arbor.Arbor
   ~ytree.arbor.arbor.Arbor.save_arbor
   ~ytree.arbor.arbor.Arbor.select_halos
   ~ytree.arbor.tree_node.TreeNode.save_tree
   ~ytree.arbor.arbor.Arbor.set_selector
   ~ytree.arbor.tree_node_selector.TreeNodeSelector
   ~ytree.arbor.tree_node_selector.add_tree_node_selector
   ~ytree.arbor.tree_node_selector.max_field_value
   ~ytree.arbor.tree_node_selector.min_field_value

Internal Classes
----------------

.. autosummary::
   :toctree: generated/

   ~ytree.arbor.arbor.Arbor
   ~ytree.arbor.arbor.CatalogArbor
   ~ytree.arbor.fields.FieldInfoContainer
   ~ytree.arbor.fields.FieldContainer
   ~ytree.arbor.fields.FakeFieldContainer
   ~ytree.arbor.io.FieldIO
   ~ytree.arbor.io.TreeFieldIO
   ~ytree.arbor.io.DefaultRootFieldIO
   ~ytree.arbor.io.DataFile
   ~ytree.arbor.io.CatalogDataFile
   ~ytree.arbor.tree_node.TreeNode
   ~ytree.arbor.tree_node_selector.TreeNodeSelector
   ~ytree.frontends.ahf.arbor.AHFArbor
   ~ytree.frontends.ahf.fields.AHFFieldInfo
   ~ytree.frontends.ahf.io.AHFDataFile
   ~ytree.frontends.arborarbor.arbor.ArborArbor
   ~ytree.frontends.arborarbor.fields.ArborArborFieldInfo
   ~ytree.frontends.arborarbor.io.ArborArborTreeFieldIO
   ~ytree.frontends.arborarbor.io.ArborArborRootFieldIO
   ~ytree.frontends.consistent_trees.arbor.ConsistentTreesArbor
   ~ytree.frontends.consistent_trees.fields.ConsistentTreesFieldInfo
   ~ytree.frontends.consistent_trees.io.ConsistentTreesDataFile
   ~ytree.frontends.consistent_trees.io.ConsistentTreesTreeFieldIO
   ~ytree.frontends.lhalotree.arbor.LHaloTreeArbor
   ~ytree.frontends.lhalotree.fields.LHaloTreeFieldInfo
   ~ytree.frontends.lhalotree.io.LHaloTreeTreeFieldIO
   ~ytree.frontends.lhalotree.io.LHaloTreeRootFieldIO
   ~ytree.frontends.rockstar.arbor.RockstarArbor
   ~ytree.frontends.rockstar.fields.RockstarFieldInfo
   ~ytree.frontends.rockstar.io.RockstarDataFile
   ~ytree.frontends.treefarm.arbor.TreeFarmArbor
   ~ytree.frontends.treefarm.fields.TreeFarmFieldInfo
   ~ytree.frontends.treefarm.io.TreeFarmDataFile
   ~ytree.frontends.treefarm.io.TreeFarmTreeFieldIO
   ~ytree.frontends.ytree.arbor.YTreeArbor
   ~ytree.frontends.ytree.io.YTreeDataFile
   ~ytree.frontends.ytree.io.YTreeTreeFieldIO
   ~ytree.frontends.ytree.io.YTreeRootFieldIO
