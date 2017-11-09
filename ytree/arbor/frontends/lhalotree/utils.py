"""
LHaloTree utilities



"""

import numpy as np
from numpy.lib.recfunctions import append_fields
import os
import glob


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
        parameter_file (str, optional): Full path to file that contains
            simulation parameters. If not provided, one with the suffix '.param'
            is searched for in the same directory as the tree file. An IOError
            will be raised if it cannot be found.
        scale_factor_file (str, optional): Full path to the file containing the
            list of scale factors for each snapshot. If not provided, one with
            the suffix '.a_list' is searched for in the same directory as the
            tree file. An IOError will be raised if it cannot be found.
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
        silent (bool, optional): If True, diagnositic info is not printed.
            Defaults to False.

    Attributes:
        filename (str): Full path to file that trees should be read from.
        parameter_file (str): Full path to file that contains simulation
            parameters.
        header_size (int): The size of the file header.
        nhalos_per_tree (np.ndarray): The number of halos in each of the ntree
            trees in the file.
        item_dtype (np.dtype): Data type specifying the structure of single halo
            entries in the tree.
        raw_fields (list): Available fields that are present for each halo based
            on item_dtype.
        add_fields (list): Calculated fields that will be added to trees as they
            are read.
        fields (list): All available fields that are present for each halo.
        filenum (int): Index of this file in the complete set for all trees.
        scale_factor_file (str): Full path to the file containing the list of
            scale factors for each snapshot.

    Raises:
        IOError: If filename is not a valid path.
        IOError: If a parameter_file is not provided or is not a valid path.
        IOError: If a scale_factor_file is not provided and cannot be found.
        IOError: If the file dosn't have the expected number of bytes.

    """

    def __init__(self, filename, parameter_file=None, scale_factor_file=None,
                 header_size=None, nhalos_per_tree=None, read_header_func=None,
                 item_dtype=None, silent=False):
        # Files
        self.filename = self._verify_file(filename)
        self.parameter_file = self._verify_file(parameter_file, suffix='.param',
                                                error_tag='Parameter file',
                                                silent=silent)
        self._parameters = None
        self.scale_factor_file = self._verify_file(scale_factor_file,
                                                   suffix='.a_list',
                                                   error_tag='Scale factor file',
                                                   silent=silent)
        self._scale_factors = None
        # Header info
        if (header_size is None) or (nhalos_per_tree is None):
            if (read_header_func is None):
                read_header_func = read_header_default
            header_size, nhalos_per_tree = read_header_func(filename)
        if (item_dtype is None):
            item_dtype = dtype_header_default
        self.header_size = header_size
        self.nhalos_per_tree = nhalos_per_tree
        self.item_dtype = np.dtype(item_dtype)
        # Fields
        self.raw_fields = list(self.item_dtype.fields.keys())
        self.add_fields = ['desc_uid', 'scale_factor',
                           'x', 'y', 'z', 'vx', 'vy', 'vz']
        self.fields = self.raw_fields + self.add_fields
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
        # Read first halo to get file number
        out = self.read_single_halo(0, 0)
        self.filenum = out[0]['FileNr']

    def _verify_file(self, filename, suffix=None, error_tag=None, silent=False):
        r"""Verify that the provided file exists. If it is None, and a suffix
        is provided, the file will be searched for in the same directory as
        self.filename.

        Args:
            filename (str): Full path that should be verified or None if the
                file should be searched for.
            suffix (str, optional): Suffix that should be used to search for a
                file if filename is None or dosn't exist. Defaults to None and
                no search is performed.
            error_tag (str, optional): Tag to use for error message in case
                where file dosn't exist. Defaults to None and 'File' is used.
            silent (bool, optional): If True, messages about located files are
                not printed. Defaults to False.

        Returns:
            str: Verified full path to the file.

        Raises:
            IOError: If filename is not a valid path and suffix is None.
            IOError: If a filename matching suffix cannot be located.

        """
        if error_tag is None:
            error_tag = 'File'
        if (filename is None) or (not os.path.isfile(filename)):
            if suffix is None:
                raise IOError("%s dosn't exist: %s" % (error_tag, filename))
            pattern = os.path.join(os.path.dirname(self.filename), '*' + suffix)
            files = glob.glob(pattern)
            if len(files) == 0:
                raise IOError("%s could not be located matching: %s" % (
                    error_tag, pattern))
            else:
                filename = files[0]
                if not silent:
                    print("Using %s found at %s" % (error_tag.lower(), filename))
        return filename

    @property
    def totnhalos(self):
        r"""int: Total number of halos in this file."""
        return sum(self.nhalos_per_tree)

    @property
    def ntrees(self):
        r"""int: Number of trees in this file."""
        return len(self.nhalos_per_tree)

    @property
    def parameters(self):
        r"""dict: Key/value pairs read from the parameter file."""
        if self._parameters is None:
            self._parameters = dict()
            with open(self.parameter_file, 'r') as fd:
                for line in fd:
                    line_strip = line.strip()
                    if len(line_strip) == 0:
                        continue
                    line_vars = line_strip.split()
                    if len(line_vars) != 2:
                        continue
                    self._parameters[line_vars[0]] = line_vars[1]
        return self._parameters

    @property
    def hubble_constant(self):
        r"""float: Hubble constants."""
        return float(self.parameters['HubbleParam'])

    @property
    def omega_matter(self):
        r"""float: Matter energy density."""
        return float(self.parameters['Omega0'])

    @property
    def omega_lambda(self):
        r"""float: Dark matter energy density."""
        return float(self.parameters['OmegaLambda'])

    @property
    def box_size(self):
        r"""float: Size of periodic boundaries."""
        return float(self.parameters['BoxSize'])

    @property
    def periodic(self):
        r"""bool: Does the simulation have periodic boundaries or not."""
        return bool(int(self.parameters['PeriodicBoundariesOn']))

    @property
    def comoving(self):
        r"""bool: Is the simulation in comoving units."""
        return bool(int(self.parameters['ComovingIntegrationOn']))

    @property
    def units_vel(self):
        r"""str: Units of velocity."""
        # out = "%s cm/s" % self.parameters['UnitVelocity_in_cm_per_s']
        u_cms = float(self.parameters['UnitVelocity_in_cm_per_s'])
        out = "%f km/s" % (u_cms/1e5)
        # TODO: Does this need adjusted for comoving?
        return out

    @property
    def units_len(self):
        r"""str: Units of length."""
        # out = "%s cm" % self.parameters['UnitLength_in_cm']
        u_cm = float(self.parameters['UnitLength_in_cm'])
        out = "%f*kpc" % (u_cm/3.085678e21)
        if self.comoving:
            out += "/h"
        return out

    @property
    def units_mass(self):
        r"""str: Units of mass."""
        # out = "%s g" % self.parameters['UnitMass_in_g']
        u_g = float(self.parameters['UnitMass_in_g'])
        out = "%f Msun" % (u_g/1.989e33)
        if self.comoving:
            out += "/h"
        return out

    @property
    def scale_factors(self):
        r"""np.ndarray: Array of scale factors at each snapshot."""
        if self._scale_factors is None:
            self._scale_factors = np.fromfile(self.scale_factor_file, sep='\n')
        return self._scale_factors

    def get_lhalotree_offset(self, treenum):
        r"""Get the offset in bytes of a tree from the beginning of the file.

        Args:
            treenum (int): Index of the tree to compute the offset of.

        Returns:
            int: Number of bytes from beginning of the file to the start of the
                requested tree.

        """
        offset = self.header_size + (sum(self.nhalos_per_tree[:treenum]) *
                                     self.item_dtype.itemsize)
        return offset

    def get_halo_offset(self, treenum, halonum):
        r"""Get the offset in bytes of a halo from the beginning of the file.

        Args:
            treenum (int): Index of the tree that requested halo is in.
            halonum (int): Index of the requested in halo in the tree.

        Returns:
            int: Number of bytes from beginning of the file to the start of the
                requested halo.

        """
        offset = self.get_lhalotree_offset(treenum)
        offset += halonum * self.item_dtype.itemsize
        return offset

    def get_lhalotree_uid(self, treenum):
        r"""Get a unique ID for this tree. Currently, the subhalo ID of the root
        is used.
        
        Args:
            treenum (int): Index of the tree to get a unique ID for.

        Returns:
            int: A unique ID for this tree.

        """
        out = self.read_single_halo(treenum, 0)
        return out[0]['SubhaloIndex']

    def read_single_halo(self, treenum, halonum, fd=None, skip_add_fields=False):
        r"""Read a single halo entry from a tree in the file.

        Args:
            treenum (int): Index of the tree that contains the requested halo.
            halonum (int): Index of the halo within its tree.
            fd (file, optional): Open file identifier. If not provided, the file
                is opened for the read and then closed.
            skip_add_fields (bool, optional): If True, the calculated fields
                will not be added or checked for. Defaults to False.

        Returns:
            np.ndarray: Single element structured array with fields for the
                corresponding halo.

        """
        offset = self.get_halo_offset(treenum, halonum)
        opened = False
        if fd is None:
            fd = open(self.filename, 'rb')
            opened = True
        fd.seek(offset, os.SEEK_SET)
        out = np.fromfile(fd, dtype=self.item_dtype, count=1)
        if opened:
            fd.close()
        # Validate
        self.validate_halo(out)
        # Add fields
        if not skip_add_fields:
            out = self.add_computed_fields(treenum, out)
        return out

    def read_single_lhalotree(self, treenum, fd=None):
        r"""Read a single lhalotree from the file.

        Args:
            treenum (int): Index of the tree that should be read from the file.
                (starts at 0)
            fd (file, optional): Open file identifier. If not provided, the file
                is opened for the read and then closed.

        Returns:
            np.ndarray: Structured array with fields for each halo in the
                corresponding tree.

        """
        offset = self.get_lhalotree_offset(treenum)
        opened = False
        if fd is None:
            fd = open(self.filename, 'rb')
            opened = True
        fd.seek(offset, os.SEEK_SET)
        out = np.fromfile(fd, dtype=self.item_dtype,
                          count=self.nhalos_per_tree[treenum])
        if opened:
            fd.close()
        # Validate
        self.validate_tree(treenum, out)
        # Add fields
        out = self.add_computed_fields(treenum, out)
        return out

    def add_computed_fields(self, treenum, tree):
        r"""Add computed fields to the numpy array.

        Args:
            treenum (int): Index of tree in file.
            tree (np.ndarray): Structured data for each halo in the tree.

        Returns:
            np.ndarray: Structured data for each halo in the tree with added
                fields.

        """
        nhalos = len(tree)
        # Descendant unique ID
        desc_uid = np.zeros(nhalos, dtype='i4')
        for h in range(nhalos):
            desc = tree[h]['Descendant']
            if desc > -1:
                if nhalos == 1:
                    desc_out = self.read_single_halo(self, treenum, desc,
                                                     skip_add_fields=True)
                    desc_uid[h] = desc_out[0]['SubhaloIndex']
                else:
                    desc_uid[h] = tree[desc]['SubhaloIndex']
            else:
                desc_uid[h] = -1
        # Scale factors
        scale_factor = self.scale_factors[tree['SnapNum']]
        # Position x, y, z
        x = tree['Pos'][:, 0]
        y = tree['Pos'][:, 1]
        z = tree['Pos'][:, 2]
        # Velocity x, y, z
        vx = tree['Vel'][:, 0]
        vy = tree['Vel'][:, 1]
        vz = tree['Vel'][:, 2]
        # Add new fields
        new_fields = dict(desc_uid=desc_uid, scale_factor=scale_factor,
                          x=x, y=y, z=z, vx=vx, vy=vy, vz=vz)
        out = append_fields(tree, new_fields.keys(), new_fields.values())
        self.validate_fields(out)
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

        """
        # Check size
        nhalos = self.nhalos_per_tree[treenum]
        assert(len(tree) == nhalos)
        # Check fields
        fields = tree.dtype.fields
        for k in self.raw_fields:
            assert(k in fields)
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

    def validate_halo(self, halo):
        r"""Check that the halo conforms to expectations.

        Args:
            halo (np.ndarray): Single element structured array of information
                for a single halo.

        Raises:
            AssertionError: If the halo does not have length of 1.
            AssertionError: If the halo does not have all of the expected fields
                from the default LHaloTree format.

        """
        # Check size
        assert(len(halo) == 1)
        # Check fields
        fields = halo.dtype.fields
        for k in self.raw_fields:
            assert(k in fields)

    def validate_fields(self, tree):
        r"""Check that the tree/halo has all of the expected fields.

        Args:
            tree (np.ndarray): Structured array of information for one or more
                halos.

        Raises:
            AssertionError: If the tree does not have all of the expected fields.

        """
        # Check fields
        fields = tree.dtype.fields.keys()
        for k in self.fields:
            assert(k in fields)
