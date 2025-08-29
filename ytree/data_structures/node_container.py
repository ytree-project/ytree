import numpy as np
import types

from ytree.data_structures.fields import FieldContainer

_selection_types = ("forest", "tree", "prog")


class NodeContainer:
    """
    A container to hold a persistent collection of unrelated TreeNodes.

    This is a convenience object to hold a series of TreeNodes
    and provide simple field access similar to querying fields
    for an entire arbor. Field access for the container is cached
    for fast second-time access.

    Parameters
    ----------

    nodes : Iterable of TreeNodes
       A list, array, or generator of TreeNode objects.

    Examples
    --------

    >>> import ytree
    >>> a = ytree.load("tiny_ctrees/locations.dat")
    >>> first = a[0]
    >>> last = a[-1]
    >>> container = a.container([first, last])
    >>> for node in container:
    >>>     print (node["mass"])
    1.0231655e+12 Msun
    2.0633094e+11 Msun
    >>> print (container["mass"])
    [1.0231655e+12 2.0633094e+11] Msun
    >>> fn = a.save_arbor(trees=container)
    >>> a_new = ytree.load(fn)
    >>> print (a_new["mass"])
    [1.0231655e+12 2.0633094e+11] Msun

    >>> import ytree
    >>> a = ytree.load("tiny_ctrees/locations.dat")
    >>> a_slice = a.container(a[::8])
    >>> print (a.size, a_slice.size)
    32 4
    >>> print (a_slice["mass"])
    [1.0231655e+12 6.7683457e+11 2.9294966e+11 2.8014389e+11] Msun
    >>> my_tree = a_slice[0]
    >>> print (my_tree)
    TreeNode[1457223360]

    >>> import ytree
    >>> a = ytree.load("tiny_ctrees/locations.dat")
    >>> my_tree = a[0]
    >>> leaves = my_tree.get_leaf_nodes()
    >>> leaf_container = a.container(leaves)
    >>> print (leaf_container["mass"])
    [2.6503598e+08 4.2388490e+08 5.6964032e+08 5.5640288e+08 3.5769786e+08
     1.9870504e+08 6.3597126e+08] Msun
    >>> print (leaf_container.nodes)
    [TreeNode[1169524360], TreeNode[758740170], TreeNode[278238650],
     TreeNode[142383462], TreeNode[38885675], TreeNode[19602159],
     TreeNode[5057761]]

    """

    def __init__(self, nodes, arbor=None):
        self._nodes = nodes
        self.field_data = FieldContainer(arbor)

    @property
    def nodes(self):
        if isinstance(self._nodes, types.GeneratorType):
            self._nodes = list(self._nodes)
        return self._nodes

    def __len__(self):
        return len(self.nodes)

    @property
    def size(self):
        return self.__len__()

    def __iter__(self):
        for node in self.nodes:
            yield node

    def __getitem__(self, key):
        if isinstance(key, str):
            if key in _selection_types:
                raise SyntaxError("Argument must be a field or integer.")

            if key not in self.field_data:
                self.field_data[key] = self.field_data.arbor.arr(
                    [tree[key] for tree in self.nodes]
                )
            return self.field_data[key]

        if isinstance(key, (int, np.integer, slice)):
            return self.nodes[key]

        else:
            raise ValueError(f"Unrecognized argument type: {key} ({type(key)}).")
