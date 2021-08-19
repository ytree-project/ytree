"""
AnalysisPipeline class and member functions



"""

import os

from yt.utilities.parallel_tools.parallel_analysis_interface import parallel_root_only

from ytree.analysis.analysis_operators import AnalysisOperation
from ytree.utilities.io import ensure_dir

class AnalysisPipeline:
    def __init__(self, output_dir=None):
        self.actions = []
        if output_dir is None:
            output_dir = "."
        self.output_dir = ensure_dir(output_dir)
        self._preprocessed = False

    def add_operation(self, function, *args, **kwargs):
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
        function : callable
            The function to be called for each node/halo.
        args : positional arguments
            Any additional positional arguments to be provided to the funciton.
        kwargs : keyword arguments
            Any keyword arguments to be provided to the function.
        """

        if not callable(function):
            raise ValueError("function argument must be a callable function.")

        operation = AnalysisOperation(function, *args, **kwargs)
        self.actions.append(operation)

    def add_recipe(self, function, *args, **kwargs):
        """
        Add a recipe to the AnalysisPipeline.

        An recipe is a function that accepts an AnalysisPipeline and adds a
        series of operations with calls to add_operation. This is a way of
        creating a shortcut for a series of operations.

        Parameters
        ----------
        function : callable
            A function accepting an AnalysisPipeline object.
        args : positional arguments
            Any additional positional arguments to be provided to the funciton.
        kwargs : keyword arguments
            Any keyword arguments to be provided to the function.
        """

        if not callable(function):
            raise ValueError("function argument must be a callable function.")

        recipe = AnalysisOperation(function, *args, **kwargs)
        recipe(self)

    @parallel_root_only
    def _preprocess(self):
        "Create output directories and do any other preliminary steps."

        if self._preprocessed:
            return

        for action in self.actions:
            my_output_dir = action.kwargs.get("output_dir")
            if my_output_dir is not None:
                new_output_dir = ensure_dir(
                    os.path.join(self.output_dir, my_output_dir))
                action.kwargs["output_dir"] = new_output_dir

        self._preprocessed = True

    def process_target(self, target):
        self._preprocess()
        target_filter = True
        for action in self.actions:
            rval = action(target)
            if rval in (True, False):
                target_filter = rval
            if not target_filter:
                break

        return target_filter
