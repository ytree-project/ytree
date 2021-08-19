"""
AnalysisPipeline operators



"""

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

    Parameters
    ----------
    function : callable
        A function that minimally accepts a
        :class:`~ytree.data_structures.tree_node.TreeNode` object. The
        function may also accept additional positional and keyword arguments.
    """
    def __init__(self, function, *args, **kwargs):
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def __call__(self, target):
        return self.function(target, *self.args, **self.kwargs)
