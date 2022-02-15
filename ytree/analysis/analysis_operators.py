"""
AnalysisPipeline operators



"""

class AnalysisOperation:
    """
    An analysis task performed by an AnalysisPipeline.

    This is an internal class that facilitates keeping track of a
    function, arguments, and keyword arguments that together represent a
    single operation in a pipeline.

    Parameters
    ----------
    function : callable
        A function that minimally accepts a
        :class:`~ytree.data_structures.tree_node.TreeNode` object. The
        function may also accept additional positional and keyword arguments.
    """
    def __init__(self, function, *args, always_do=False, **kwargs):
        self.function = function
        self.always_do = always_do
        self.args = args
        self.kwargs = kwargs

    def __call__(self, target):
        return self.function(target, *self.args, **self.kwargs)
