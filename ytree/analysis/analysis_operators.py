"""
AnalysisPipeline operators



"""

import copy

class OperatorRegistry(dict):
    def find(self, op, *args, **kwargs):
        if isinstance(op, str):
            op = copy.deepcopy(self[op])
            op.args = args
            op.kwargs = kwargs
        return op


class AnalysisOperation:
    """
    An analysis task performed by an AnalysisPipeline.

    An AnalysisOperation is a function that minimally takes in a target object
    and performs some actions on or with it. This function may alter the
    object's state, attach attributes, write out data, etc. AnalysisOperations
    are used to create a pipeline of actions performed in sequence on a list
    of objects, such as all halos in a merger tree. The function can,
    optionally, return True or False to act as a filter, determining if the
    rest of the pipeline should be carried out (if True) or if the pipeline
    should stop and move on to the next object (if False).
    """
    def __init__(self, function, args=None, kwargs=None):
        self.function = function
        if args is None:
            args = []
        self.args = args
        if kwargs is None:
            kwargs = {}
        self.kwargs = kwargs

    def __call__(self, target):
        return self.function(target, *self.args, **self.kwargs)


operation_registry = OperatorRegistry()

def add_operation(name, function):
    """
    Add an operation to the operation registry.

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
        The name the recipe will be stored under in the registry.
    function : callable
        A function accepting an AnalysisPipeline object.
    """
    operation_registry[name] =  AnalysisOperation(function)

recipe_registry = OperatorRegistry()

def add_recipe(name, function):
    """
    Add a recipe to the recipe registry.

    An recipe is a function that accepts an AnalysisPipeline and
    adds a series of operations. This is a way of creating a
    shortcut for a series of operations.

    Parameters
    ----------
    name : str
        The name the recipe will be stored under in the registry.
    function : callable
        A function accepting an AnalysisPipeline object.
    """
    recipe_registry[name] =  AnalysisOperation(function)
