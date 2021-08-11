"""
AnalysisPipeline class and member functions



"""

import os

from yt.utilities.parallel_tools.parallel_analysis_interface import parallel_root_only

from ytree.analysis.analysis_operators import \
    operation_registry, \
    recipe_registry
from ytree.utilities.io import ensure_dir

class AnalysisPipeline:
    def __init__(self, output_dir=None):
        self.actions = []
        if output_dir is None:
            output_dir = "."
        self.output_dir = ensure_dir(output_dir)
        self._preprocessed = False

    def add_operation(self, name, *args, **kwargs):
        """
        Add an operation to the AnalysisPipeline.

        An operation is a function that minimally takes in a target object
        and performs some actions on or with it. This function may alter the
        object's state, attach attributes, write out data, etc. Operations
        are used to create a pipeline of actions performed in sequence on a list
        of objects, such as all halos in a merger tree. The function can,
        optionally, return True or False to act as a filter, determining if the
        rest of the pipeline should be carried out (if True) or if the pipeline
        should stop and move on to the next object (if False).

        Parameters
        ----------
        name : str
            The name of the operation in the registry.
        """
        name = operation_registry.find(name, *args, **kwargs)
        self.actions.append(("operation", name))

    def add_recipe(self, name, *args, **kwargs):
        """
        Add a recipe to the AnalysisPipeline.

        An recipe is a function that accepts an AnalysisPipeline and
        adds a series of operations. This is a way of creating a
        shortcut for a series of operations.

        Parameters
        ----------
        name : str
            The name of the recipe in the registry.
        """
        analysis_recipe = recipe_registry.find(name, *args, **kwargs)
        analysis_recipe(self)

    @parallel_root_only
    def _preprocess(self):
        "Create output directories and do any other preliminary steps."

        if self._preprocessed:
            return

        for action_type, action in self.actions:
            if action_type != "operation":
                continue
            my_output_dir = action.kwargs.get("output_dir")
            if my_output_dir is not None:
                new_output_dir = ensure_dir(
                    os.path.join(self.output_dir, my_output_dir))
                action.kwargs["output_dir"] = new_output_dir

        self._preprocessed = True

    def process_target(self, target):
        self._preprocess()
        target_filter = True
        for action_type, action in self.actions:
            if action_type == "operation":
                rval = action(target)
                if rval in (True, False):
                    target_filter = rval
                if not target_filter:
                    break
            else:
                raise RuntimeError("Action must be an operation.")

        return target_filter
