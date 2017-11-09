"""
LHaloTree utilities



"""

import numpy as np
import os


"""Default header data type."""
dtype_header_default = [
    # merger tree pointers
    ('Descendant', 'i4'),
    ('FirstProgenitor', 'i4'),
    ('NextProgenitor', 'i4'),
    ('FirstHaloInFOFgroup', 'i4'),
    ('NextHaloInFOFgroup', 'i4'),
    # properties of halo
    ('Len', 'i4'),
    ('M_Mean200', 'f4'),
    ('Mvir', 'f4'), # for Millennium, Mvir=M_Crit200
    ('M_TopHat', 'f4'),
    ('Pos', 'f4', 3),
    ('Vel', 'f4', 3),
    ('VelDisp', 'f4'),
    ('Vmax', 'f4'),
    ('Spin', 'f4', 3),
    ('MostBoundID', 'i8'),
    # original position in simulation tree files
    ('SnapNum', 'i4'),
    ('FileNr', 'i4'),
    ('SubhaloIndex', 'i4'),
    ('SubHalfMass', 'f4')]
halo_fields = ['Descendant', 'FirstProgenitor', 'NextProgenitor',
               'FirstHaloInFOFgroup', 'NextHaloInFOFgroup']


def read_header_default(filename):
    r"""Reads the default LHaloTree file header.

    Args:
        filename (str): Full path to file that header should be read from.

    Returns:
         tuple (int, np.ndarray): The size of the file header and the number
             of halos in each header.

    """
    with open(filename, 'rb') as fd:
        dtype1 = np.dtype([('ntrees', 'i4'), ('totnhalos', 'i4')])
        x1 = np.fromfile(fd, dtype=dtype1, count=1)
        ntrees = x1['ntrees'][0]
        nhalos = x1['totnhalos'][0]
        dtype2 = np.dtype('i4')
        x2 = np.fromfile(fd, dtype=dtype2, count=ntrees)
        assert(len(x2) == ntrees)
        assert(sum(x2) == nhalos)
        header_size = dtype1.itemsize + ntrees*dtype2.itemsize
    return header_size, x2


class LHaloTreeReader(object):
    r"""Class for reading halos from an LHaloTree file.

    Args:
        filename (str): Full path to file that trees should be read from.
        header_size (int, optional): The size of the file header. If not
            provided, it will be obtained from read_header_func.
        nhalos_per_tree (np.ndarray, optional): The number of halos in each of
            the ntree trees in the file. If not provided, it will be obtained
            from read_header_func.
        read_header_func (obj, optional): Callable object that takes a filename
            and returns the size of the file header and the number of halos in
            each tree in the file. Defaults to read_header_default.
        item_dtype (obj, optional): np.dtype or object that can be converted
            into a numpy dtype specifying the structure of single halo entries
            in the tree. Defaults to dtype_header_default.

    Attributes:
        filename (str): Full path to file that trees should be read from.
        header_size (int): The size of the file header.
        nhalos_per_tree (np.ndarray): The number of halos in each of the ntree
            trees in the file.
        item_dtype (np.dtype): Data type specifying the structure of single halo
            entries in the tree.

    Raises:
        IOError: If filename is not a valid path.
        IOError: If the file dosn't have the expected number of bytes.

    """

    def __init__(self, filename, header_size=None, nhalos_per_tree=None,
                 read_header_func=None, item_dtype=None):
        if not os.path.isfile(filename):
            raise IOError("File dosn't exists: %s" % filename)
        self.filename = filename
        if (header_size is None) or (nhalos_per_tree is None):
            if (read_header_func is None):
                read_header_func = read_header_default
            header_size, nhalos_per_tree = read_header_func(filename)
        if (item_dtype is None):
            item_dtype = dtype_header_default
        self.header_size = header_size
        self.nhalos_per_tree = nhalos_per_tree
        self.item_dtype = np.dtype(item_dtype)
        # Check file size
        item_size = self.item_dtype.itemsize
        body_size = self.totnhalos * item_size
        file_size = os.stat(self.filename).st_size
        if body_size != file_size - self.header_size:
            raise IOError(
                ("File is %d bytes, but %d items of size %d " +
                 "with header of %d bytes should be %d bytes total.") \
                 % (file_size, self.totnhalos, item_size,
                    self.header_size, body_size + self.header_size))

    @property
    def totnhalos(self):
        r"""int: Total number of halos in this file."""
        return sum(self.nhalos_per_tree)

    @property
    def ntrees(self):
        r"""int: Number of trees in this file."""
        return len(self.nhalos_per_tree)

    def read_single_lhalotree(self, treenum):
        r"""Read a single lhalotree from the file.

        Args:
            treenum (int): Index of the tree that should be read from the file.
                (starts at 0)

        Returns:
            np.ndarray: Single element structured array with fields for the
                corresponding tree.

        """
        offset = self.header_size + (sum(self.nhalos_per_tree[:treenum]) *
                                     self.item_dtype.itemsize)
        with open(self.filename, 'rb') as fd:
            fd.seek(offset, os.SEEK_SET)
            out = np.fromfile(fd, dtype=self.item_dtype,
                              count=self.nhalos_per_tree[treenum])
        self.validate_tree(treenum, out)
        return out

    def validate_tree(self, treenum, tree):
        r"""Check that the tree conforms to expectation.

        Args:
            treenum (int): Index of the tree being validated in the file.
            tree (np.ndarray): Structured array of information for halos in a
                tree.

        Raises:
            AssertionError: If the tree does not have the expected number of
                halos.
            AssertionError: If the tree does not have all of the expected fields
                from the default LHaloTree format.
            AssertionError: If any of the halos have fields pointing to halos
                outside the tree (indicies exceeding nhalos).
            AssertionError: If there are any halos in a FOF group that are not
                in the same snapshot as the central.
            AssertionError: If the progenitors/descendants of any halo are not
                backwards/forwards in time.
            AssertionError:

        """
        # Check size
        nhalos = self.nhalos_per_tree[treenum]
        assert(len(tree) == nhalos)
        # Check fields
        fields = tree.dtype.fields
        for k in dtype_header_default:
            assert(k[0] in fields)
        # Check that halos are within tree
        for k in halo_fields:
            pos_flag = (tree[k] >= 0)
            assert((tree[k][pos_flag] <= nhalos).all())
        # Check FOF all in one snapshot
        for h in range(nhalos):
            central = tree[h]['FirstHaloInFOFgroup']
            assert(tree[h]['SnapNum'] == tree[central]['SnapNum'])
        # Check that progenitors/descendants are back/forward in time
        for h in range(nhalos):
            progen1 = tree[h]['FirstProgenitor']
            progen2 = tree[h]['NextProgenitor']
            descend = tree[h]['Descendant']
            if descend >= 0:
                assert(tree[descend]['SnapNum'] > tree[h]['SnapNum'])
            else:
                descend = h
            # TODO: Can 1st progenitor be in the same snapshot as a halo?
            if progen1 >= 0:
                assert(tree[progen1]['SnapNum'] <= tree[descend]['SnapNum'])
            if progen2 >= 0:
                assert(tree[progen2]['SnapNum'] <= tree[descend]['SnapNum'])
