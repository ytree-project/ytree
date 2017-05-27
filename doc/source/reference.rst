.. _api-reference:

API Reference
=============

Working with Merger-Trees
-------------------------

The :ref:`~ytree.arbor.load` can load all supported
merger-tree formats.  Once loaded, the
:ref:`~ytree.arbor.Arbor.save_arbor` and
:reF:`~ytree.tree_node.TreeNode.save_tree` functions can be
used to save the entire arbor or individual trees.

.. autosummary::
   :toctree: generated/

   ~ytree.arbor.load
   ~ytree.arbor.Arbor.save_arbor
   ~ytree.tree_node.TreeNode.save_tree
   ~ytree.tree_node.TreeNode._line
   ~ytree.tree_node.TreeNode._tree
   ~ytree.arbor.Arbor.set_selector
   ~ytree.tree_node_selector.TreeNodeSelector
   ~ytree.tree_node_selector.add_tree_node_selector
   ~ytree.tree_node_selector.max_field_value
   ~ytree.tree_node_selector.min_field_value

Making Merger-Trees
-------------------

.. autosummary::
   :toctree: generated/

   ~ytree.tree_farm.TreeFarm
   ~ytree.tree_farm.TreeFarm.trace_ancestors
   ~ytree.tree_farm.TreeFarm.trace_descendents
   ~ytree.tree_farm.TreeFarm.set_selector
   ~ytree.tree_farm.TreeFarm.set_ancestry_checker
   ~ytree.tree_farm.TreeFarm.set_ancestry_filter
   ~ytree.tree_farm.TreeFarm.set_ancestry_short
   ~ytree.ancestry_checker.AncestryChecker
   ~ytree.ancestry_checker.add_ancestry_checker
   ~ytree.ancestry_checker.common_ids
   ~ytree.ancestry_filter.AncestryFilter
   ~ytree.ancestry_filter.add_ancestry_filter
   ~ytree.ancestry_filter.most_massive
   ~ytree.ancestry_short.AncestryShort
   ~ytree.ancestry_short.add_ancestry_short
   ~ytree.ancestry_short.above_mass_fraction
   ~ytree.halo_selector.HaloSelector
   ~ytree.halo_selector.add_halo_selector
   ~ytree.halo_selector.sphere_selector
   ~ytree.halo_selector.all_selector

Internal Classes
----------------

.. autosummary::
   :toctree: generated/

   ~ytree.arbor.Arbor
   ~ytree.arbor.ArborArbor
   ~ytree.arbor.CatalogArbor
   ~ytree.arbor.ConsistentTreesArbor
   ~ytree.arbor.RockstarArbor
   ~ytree.arbor.TreeFarmArbor
   ~ytree.tree_node.TreeNode
