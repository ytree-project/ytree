.. _api-reference:

API Reference
=============

Working with Merger Trees
-------------------------

The :func:`~ytree.data_structures.arbor.load` can load all supported
merger tree formats.  Once loaded, the
:func:`~ytree.data_structures.arbor.Arbor.save_arbor` and
:func:`~ytree.data_structures.tree_node.TreeNode.save_tree` functions can be
used to save the entire arbor or individual trees.

.. autosummary::
   :toctree: generated/

   ~ytree.data_structures.arbor.load
   ~ytree.data_structures.arbor.Arbor
   ~ytree.data_structures.arbor.Arbor.add_alias_field
   ~ytree.data_structures.arbor.Arbor.add_analysis_field
   ~ytree.data_structures.arbor.Arbor.add_derived_field
   ~ytree.data_structures.arbor.Arbor.save_arbor
   ~ytree.data_structures.arbor.Arbor.select_halos
   ~ytree.data_structures.tree_node.TreeNode.save_tree
   ~ytree.data_structures.arbor.Arbor.set_selector
   ~ytree.data_structures.tree_node_selector.TreeNodeSelector
   ~ytree.data_structures.tree_node_selector.add_tree_node_selector
   ~ytree.data_structures.tree_node_selector.max_field_value
   ~ytree.data_structures.tree_node_selector.min_field_value

Visualizing Merger Trees
------------------------

Functionality for plotting merger trees.

.. autosummary::
   :toctree: generated/

   ~ytree.visualization.tree_plot.TreePlot
   ~ytree.visualization.tree_plot.TreePlot.save

Internal Classes
----------------

.. autosummary::
   :toctree: generated/

   ~ytree.data_structures.arbor.Arbor
   ~ytree.data_structures.arbor.CatalogArbor
   ~ytree.data_structures.fields.FieldInfoContainer
   ~ytree.data_structures.fields.FieldContainer
   ~ytree.data_structures.fields.FakeFieldContainer
   ~ytree.data_structures.io.FieldIO
   ~ytree.data_structures.io.TreeFieldIO
   ~ytree.data_structures.io.DefaultRootFieldIO
   ~ytree.data_structures.io.DataFile
   ~ytree.data_structures.io.CatalogDataFile
   ~ytree.data_structures.tree_node.TreeNode
   ~ytree.data_structures.tree_node_selector.TreeNodeSelector
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
