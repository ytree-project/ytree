"""
AnalysisPipeline class and member functions



"""

import os

from yt.utilities.parallel_tools.parallel_analysis_interface import parallel_root_only

from ytree.analysis.analysis_operators import AnalysisOperation
from ytree.utilities.io import ensure_dir


class AnalysisPipeline:
    """
    Initialize an AnalysisPipeline.

    An AnalysisPipeline allows one to create a workflow of analysis to be
    performed on a node/halo in a tree. This is done by creating functions
    that minimally accept a node as the first argument and providing these
    to the AnalysisPipeline in the order they are meant to be run. This
    makes it straightforward to organize an analysis workflow into a series
    of distinct, reusable functions.

    Parameters
    ----------
    output_dir : optional, str
        Path to a directory into which any files will be saved. The
        directory will be created if it does not already exist.

    Examples
    --------

    >>> import ytree
    >>>
    >>> def my_analysis(node):
    ...     node["test_field"] = 2 * node["mass"]
    >>>
    >>> def minimum_mass(node, value):
    ...     return node["mass"] > value
    >>>
    >>> def my_recipe(pipeline):
    ...     pipeline.add_operation(my_analysis)
    >>>
    >>> def do_cleanup(node):
    ...     print (f"End of analysis for {node}.")
    >>>
    >>> a = ytree.load("arbor/arbor.h5")
    >>>
    >>> ap = AnalysisPipeline()
    >>> # don't analyze halos below 3e11 Msun
    >>> ap.add_operation(minimum_mass, 3e11)
    >>> ap.add_recipe(my_recipe)
    >>> ap.add_recipe(do_cleanup, always_do=True)
    >>>
    >>> trees = list(a[:])
    >>> for tree in trees:
    ...     for node in tree["forest"]:
    ...         ap.process_target(node)
    >>>
    >>> a.save_arbor(trees=trees)
    """

    def __init__(self, output_dir=None):
        self.actions = []
        if output_dir is None:
            output_dir = "."
        self.output_dir = ensure_dir(output_dir)
        self._preprocess_functions = []
        self._preprocessed = False
        self._handoff_store = {}

    def add_operation(
        self, function, *args, always_do=False, preprocess_function=None, **kwargs
    ):
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
        *args : positional arguments
            Any additional positional arguments to be provided to the funciton.
        always_do : optional, bool
            If True, always perform this operation even if a prior filter has
            returned False. This can be used to add house cleaning operations
            that should always be run.
            Default: False
        preprocess_function : optional, callable
            A function to be run once at the start of analysis. This can be
            used to perform any necessary startup tasks prior to running the
            pipeline. The function provided must accept no arguments.
            Default: None
        **kwargs : keyword arguments
            Any keyword arguments to be provided to the function.
        """

        if not callable(function):
            raise ValueError("function argument must be a callable function.")

        operation = AnalysisOperation(function, *args, always_do=always_do, **kwargs)
        self.actions.append(operation)
        if preprocess_function is not None:
            self._preprocess_functions.append(preprocess_function)

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
        *args : positional arguments
            Any additional positional arguments to be provided to the funciton.
        **kwargs : keyword arguments
            Any keyword arguments to be provided to the function.

        Examples
        --------
        >>> def print_field_value(node, field):
        ...     print (f"Node {node} has {field} of {node[field]}.")
        >>>
        >>> def print_many_things(pipeline, fields):
        ...    for field in fields:
        ...        pipeline.add_operation(print_field_value, field)
        >>>
        >>> ap = ytree.AnalysisPipeline()
        >>> ap.add_recipe(print_many_things, ["mass", "virial_radius"])
        """

        if not callable(function):
            raise ValueError("function argument must be a callable function.")

        recipe = AnalysisOperation(function, *args, **kwargs)
        recipe(self)

    @parallel_root_only
    def _preprocess(self):
        """
        Create output directories and do any other preliminary steps.

        Run any preprocess functions that were added.
        """

        if self._preprocessed:
            return

        for pre_func in self._preprocess_functions:
            pre_func()

        for action in self.actions:
            my_output_dir = action.kwargs.get("output_dir")
            if my_output_dir is not None:
                new_output_dir = ensure_dir(
                    os.path.join(self.output_dir, my_output_dir)
                )
                action.kwargs["output_dir"] = new_output_dir

        self._preprocessed = True

    def process_target(self, target, handoff_attrs=None):
        """
        Process a node through the AnalysisPipeline.

        All operations added to the AnalysisPipeline will be run on the
        provided target.

        Parameters
        ----------
        target : :class:`~ytree.data_structures.tree_node.TreeNode`
            The node on which to run the analysis pipeline.
        handoff_attrs : optional, list of strings
            A list of attributes to be handed down from one target to
            the next. If given, these attributes will be taken from the
            target object after the pipeline is run and stored internally.
            They will then be attached to the next target run through the
            pipeline. This can be used to pass down attributes from
            one target to the next, for example, to accumulate results
            or hang onto objects that are expensive to create.
            Default: None.
        """

        self._preprocess()
        if handoff_attrs is None:
            handoff_attrs = []

        for attr in handoff_attrs:
            if attr in self._handoff_store:
                val = self._handoff_store.pop(attr)
                setattr(target, attr, val)

        target_filter = True
        for action in self.actions:
            if target_filter or action.always_do:
                rval = action(target)
                if rval is not None:
                    target_filter &= bool(rval)

        for attr in handoff_attrs:
            if hasattr(target, attr):
                val = getattr(target, attr)
                self._handoff_store[attr] = val
                delattr(target, attr)

        return target_filter
