import numpy as np
import types

from ytree.data_structures.fields import FieldContainer

_selection_types = ("forest", "tree", "prog")

class TreeContainer:
    def __init__(self, arbor, trees):
        self._trees = trees
        self.field_data = FieldContainer(arbor)

    @property
    def trees(self):
        if isinstance(self._trees, types.GeneratorType):
            self._trees = list(self._trees)
        return self._trees

    def __iter__(self):
        return self.trees

    def __getitem__(self, key):
        if isinstance(key, str):
            if key in _selection_types:
                raise SyntaxError("Argument must be a field or integer.")

            if key not in self.field_data:
                self.field_data[key] = self.field_data.arbor.arr(
                    [tree[key] for tree in self.trees])
            return self.field_data[key]

        if isinstance(key, (int, np.integer, slice)):
            return self.trees[key]

        else:
            raise ValueError(
                f"Unrecognized argument type: {key} ({type(key)}).")
