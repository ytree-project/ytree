"""
LHaloTreeArbor io classes and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import numpy as np
# import weakref
from ytree.data_structures.io import \
    FieldIO, \
    TreeFieldIO


# class LHaloTreeFileID:
#     r"""Handle cached file ID.

#     Args:
#         filename (str): Full path to file that should be opened for reading.

#     Attributes:
#         fd (file): Open file descriptor.

#     """
#     def __init__(self, filename):
#         self._finalizer = None
#         self.fd = None
#         self.update(filename)

#     def close(self):
#         r"""Close the file descriptor."""
#         self._finalizer()

#     def update(self, filename):
#         r"""Update the file descriptor and finalizer.

#         Args:
#             filename (str): Full path to file that should be opened for reading.

#         """
#         if (self.fd is None) or (self.fd.name != filename):
#             if self.fd is not None:
#                 self.close()
#             self.fd = open(filename, 'rb')
#             self._finalizer = weakref.finalize(self, self.fd.close)


class LHaloTreeTreeFieldIO(TreeFieldIO):

    def _read_fields(self, root_node, fields, dtypes=None,
                     f=None, root_only=False):
        """
        Read fields from disk for a single tree.

        Here we accept a list of fields and return a dictionary of NumPy
        arrays for each field.

        dtypes will be an optional dictionary of type for each field

        f will optionally be the already-opened file handle.

        If root_only is true, we only want the field value for the root
        of the tree.

        Below is the example for ctrees.
        """
        if dtypes is None:
            dtypes = {}

        lht = root_node._lht

        # This stores the file ID in a class that handles clean up via
        # weakref.finalize. The cached file object is checked to see if it
        # access the correct file for this node. If not, the cached file
        # object is closed and replaced with a file object for the correct
        # file.
        # This is only necessary if LHaloTreeReader is using np.fromfile (it
        # currently uses np.memmap).
        # Get cached fid.
        # if f is None:
        #     if not hasattr(self, '_cached_fid'):
        #         self._cached_fd = LHaloTreeFileID(lht.filename)
        #     self._cached_fd.update(lht.filename)
        #     f = self._cached_fd.fd

        # Don't read all data if only uid/desc_uid requested
        data = None
        for field in fields:
            if field not in ['uid', 'desc_uid']:
                # if root_only:
                #     data = lht.read_single_root(root_node._index_in_lht, fd=f)
                # else:
                data = lht.read_single_tree(root_node._index_in_lht, fd=f)
                break
        if data is None:
            data = dict()
            # always get all ids, even if root_only, since it's fast.
            halonum = None
            tot_idx = lht.get_total_index(root_node._index_in_lht, halonum)
            data['uid'] = lht.all_uids[tot_idx]
            data['desc_uid'] = lht.all_desc_uids[tot_idx]
        field_data = data

        self._apply_units(fields, field_data)

        return field_data


class LHaloTreeRootFieldIO(FieldIO):
    def _read_fields(self, storage_object, fields, dtypes=None):
        r"""Add root fields in bulk to same time."""
        if dtypes is None:
            dtypes = {}
        my_dtypes = self._determine_dtypes(fields, override_dict=dtypes)

        field_data = {field: np.empty(self.arbor.size, dtype=my_dtypes[field])
                      for field in fields}

        self._apply_units(fields, field_data)

        ntrees_prev = 0
        for lht in self.arbor._lhtfiles:
            ntrees = lht.ntrees
            for field in fields:
                field_data[field][ntrees_prev:(ntrees_prev + ntrees)] = \
                  lht._root_data[field]
            ntrees_prev += ntrees

        return field_data
