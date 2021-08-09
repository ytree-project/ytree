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

operation_registry = OperatorRegistry()

def add_operation(name, function):
    operation_registry[name] =  AnalysisOperation(function)

class AnalysisOperation(object):
    r"""
    An AnalysisOperation is a function that minimally takes in a target object
    and performs some analysis on it. This function may attach attributes
    to the target object, write out data, etc, but does not return anything.
    """
    def __init__(self, function, args=None, kwargs=None):
        self.function = function
        self.args = args
        if self.args is None: self.args = []
        self.kwargs = kwargs
        if self.kwargs is None: self.kwargs = {}

    def __call__(self, target):
        self.function(target, *self.args, **self.kwargs)
        return True

filter_registry = OperatorRegistry()

def add_filter(name, function):
    filter_registry[name] = AnalysisFilter(function)

class AnalysisFilter(AnalysisOperation):
    r"""
    An AnalysisFilter is a function that minimally takes a target object, performs
    some analysis, and returns either True or False. The return value determines
    whether analysis is continued.
    """
    def __init__(self, function, *args, **kwargs):
        AnalysisOperation.__init__(self, function, args, kwargs)

    def __call__(self, target):
        return self.function(target, *self.args, **self.kwargs)

recipe_registry = OperatorRegistry()

def add_recipe(name, function):
    recipe_registry[name] =  AnalysisRecipe(function)

class AnalysisRecipe(object):
    r"""
    An AnalysisRecipe is a function that accepts an AnalysisPipeline and
    adds a series of operations and filters. This is a way of creating a
    shortcut for a series of operations.
    """
    def __init__(self, function, args=None, kwargs=None):
        self.function = function
        self.args = args
        if self.args is None: self.args = []
        self.kwargs = kwargs
        if self.kwargs is None: self.kwargs = {}

    def __call__(self, pipeline):
        return self.function(pipeline, *self.args, **self.kwargs)
