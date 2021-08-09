"""
AnalysisPipeline class and member functions



"""

import os

from yt.utilities.parallel_tools.parallel_analysis_interface import parallel_root_only

from ytree.utilities.io import ensure_dir

from ytree.analysis.analysis_operators import \
    operation_registry, \
    filter_registry, \
    recipe_registry

class AnalysisPipeline:
    def __init__(self, output_dir=None):
        self.actions = []
        if output_dir is None:
            output_dir = "."
        self.output_dir = ensure_dir(output_dir)
        self._preprocessed = False

    def add_operation(self, my_operation, *args, **kwargs):
        my_operation = operation_registry.find(my_operation, *args, **kwargs)
        self.actions.append(("operation", my_operation))

    def add_filter(self, my_filter, *args, **kwargs):
        my_filter = filter_registry.find(my_filter, *args, **kwargs)
        self.actions.append(("filter", my_filter))

    def add_recipe(self, recipe, *args, **kwargs):
        analysis_recipe = recipe_registry.find(recipe, *args, **kwargs)
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
                action(target)
            elif action_type == "filter":
                target_filter = action(target)
                if not target_filter:
                    break
            else:
                raise RuntimeError(
                    "Action must be an operation or a filter.")

        return target_filter
