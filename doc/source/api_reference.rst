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

Making Merger-Trees
-------------------

.. autosummary::
   :toctree: generated/

   ~ytree.tree_farm.tree_farm.TreeFarm
   ~ytree.tree_farm.tree_farm.TreeFarm.trace_ancestors
   ~ytree.tree_farm.tree_farm.TreeFarm.trace_descendents
   ~ytree.tree_farm.tree_farm.TreeFarm.set_selector
   ~ytree.tree_farm.tree_farm.TreeFarm.set_ancestry_checker
   ~ytree.tree_farm.tree_farm.TreeFarm.set_ancestry_filter
   ~ytree.tree_farm.tree_farm.TreeFarm.set_ancestry_short
   ~ytree.tree_farm.ancestry_checker.AncestryChecker
   ~ytree.tree_farm.ancestry_checker.add_ancestry_checker
   ~ytree.tree_farm.ancestry_checker.common_ids
   ~ytree.tree_farm.ancestry_filter.AncestryFilter
   ~ytree.tree_farm.ancestry_filter.add_ancestry_filter
   ~ytree.tree_farm.ancestry_filter.most_massive
   ~ytree.tree_farm.ancestry_short.AncestryShort
   ~ytree.tree_farm.ancestry_short.add_ancestry_short
   ~ytree.tree_farm.ancestry_short.above_mass_fraction
   ~ytree.tree_farm.halo_selector.HaloSelector
   ~ytree.tree_farm.halo_selector.add_halo_selector
   ~ytree.tree_farm.halo_selector.sphere_selector
   ~ytree.tree_farm.halo_selector.all_selector

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
   ~ytree.arbor.frontends.ahf.arbor.AHFArbor
   ~ytree.arbor.frontends.ahf.fields.AHFFieldInfo
   ~ytree.arbor.frontends.ahf.io.AHFDataFile
   ~ytree.arbor.frontends.arborarbor.arbor.ArborArbor
   ~ytree.arbor.frontends.arborarbor.fields.ArborArborFieldInfo
   ~ytree.arbor.frontends.arborarbor.io.ArborArborTreeFieldIO
   ~ytree.arbor.frontends.arborarbor.io.ArborArborRootFieldIO
   ~ytree.arbor.frontends.consistent_trees.arbor.ConsistentTreesArbor
   ~ytree.arbor.frontends.consistent_trees.fields.ConsistentTreesFieldInfo
   ~ytree.arbor.frontends.consistent_trees.io.ConsistentTreesDataFile
   ~ytree.arbor.frontends.consistent_trees.io.ConsistentTreesTreeFieldIO
   ~ytree.arbor.frontends.lhalotree.arbor.LHaloTreeArbor
   ~ytree.arbor.frontends.lhalotree.fields.LHaloTreeFieldInfo
   ~ytree.arbor.frontends.lhalotree.io.LHaloTreeTreeFieldIO
   ~ytree.arbor.frontends.lhalotree.io.LHaloTreeRootFieldIO
   ~ytree.arbor.frontends.rockstar.arbor.RockstarArbor
   ~ytree.arbor.frontends.rockstar.fields.RockstarFieldInfo
   ~ytree.arbor.frontends.rockstar.io.RockstarDataFile
   ~ytree.arbor.frontends.tree_farm.arbor.TreeFarmArbor
   ~ytree.arbor.frontends.tree_farm.fields.TreeFarmFieldInfo
   ~ytree.arbor.frontends.tree_farm.io.TreeFarmDataFile
   ~ytree.arbor.frontends.tree_farm.io.TreeFarmTreeFieldIO
   ~ytree.arbor.frontends.ytree.arbor.YTreeArbor
   ~ytree.arbor.frontends.ytree.io.YTreeDataFile
   ~ytree.arbor.frontends.ytree.io.YTreeTreeFieldIO
   ~ytree.arbor.frontends.ytree.io.YTreeRootFieldIO
