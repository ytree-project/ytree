"""
LHaloTree utilities



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import numpy as np
import os
import glob

from ytree.utilities.logger import \
    ytreeLogger

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
    # Open
    if isinstance(filename, str):
        fd = open(filename, 'rb')
        close = True
    else:
        fd = filename
        close = False
    # Read
    dtype1 = np.dtype([('ntrees', 'i4'), ('totnhalos', 'i4')])
    x1 = np.fromfile(fd, dtype=dtype1, count=1)
    ntrees = x1['ntrees'][0]
    nhalos = x1['totnhalos'][0]
    dtype2 = np.dtype('i4')
    x2 = np.fromfile(fd, dtype=dtype2, count=ntrees)
    assert(len(x2) == ntrees)
    assert(np.sum(x2) == nhalos)
    header_size = dtype1.itemsize + ntrees*dtype2.itemsize
    # Close
    if close:
        fd.close()
    return header_size, x2


def save_header_default(filename, nhalos_per_tree):
    r"""Writes the default LHaloTree file header.

    Args:
        filename (str): Full path to file that should be written to.
        nhalos_per_tree (np.ndarray): The number of halos in each tree that
            will be written to the file.
    
    Returns:
        int: The size of the header that was written.

    """
    ntrees = len(nhalos_per_tree)
    nhalos = np.sum(nhalos_per_tree)
    dtype1 = np.dtype([('ntrees', 'i4'), ('totnhalos', 'i4')])
    x1 = np.array([(ntrees, nhalos)], dtype=dtype1)
    x2 = nhalos_per_tree.astype('i4')
    header_size = x1.nbytes + x2.nbytes
    # Open
    if isinstance(filename, str):
        fd = open(filename, 'wb')
        close = True
    else:
        fd = filename
        close = False
    # Write
    x1.tofile(fd)
    x2.tofile(fd)
    # Close
    if close:
        fd.close()
    return header_size


def _read_from_mmap(filename, start=0, nhalo=None,
                    header_size=None, item_dtype=None):
    r"""Read one or more halos from a memmapped file.

    Args:
        filename (str, np.memmap): Either the full path to the file that should
            be read via memmap or an existing memmapped file.
        start (int, optional): Index of halo in memmap where read should start.
            Defaults to 0.
        nhalo (int, optional): Number of halos that should be read. Defaults to
            None and all halos following start are read.
        header_size (int, optional): Size of the header preceeding trees in the
            file. If this is not provided and filename is a path, it will be set
            to 0.
        item_dtype (np.dtype, optional): Data type of each halo entry. Defaults
            to dtype_header_default.

    Returns:
        np.ndarray: Structure array of halo data.

    """
    if isinstance(filename, np.memmap):
        mmap = filename
    else:
        if header_size is None:
            header_size = 0
        if item_dtype is None:
            item_dtype = dtype_header_default
        mmap = np.memmap(filename, dtype=item_dtype, mode='c', offset=header_size)
    if nhalo is None:
        stop = None
    else:
        stop = start + nhalo
    idx = slice(start, stop)
    return mmap[idx]


def _save_to_mmap(filename, data, start=0, header_size=None):
    r"""Save one or more halos to a memmapped file.

    Args:
        filename (str, np.memmap): Either the full path to the file that should
            be saved to via memmap or an existing memmapped file.
        data (np.ndarray): Structured array of halo data that should be saved.
        start (int, optional): Index in memmap where halos should be written.
            Defaults to 0.
        header_size (int, optional): Size of the header preceeding trees in the
            file. If this is not provided and filename is a path, it will be set
            to 0.

    """
    nhalo = len(data)
    if isinstance(filename, np.memmap):
        mmap = filename
        flush = False
    else:
        if header_size is None:
            header_size = 0
        item_dtype = data.dtype
        mmap = np.memmap(filename, dtype=item_dtype, mode='r+',
                         offset=header_size, shape=(nhalo, ))
        flush = True
    mmap[start:(start + nhalo)] = data[:]
    if flush:
        del mmap  # flush to disk


def _read_from_file(filename, start=0, nhalo=None,
                    header_size=None, item_dtype=None):
    r"""Read one or more halos from the file using np.fromfile.

    Args:
        filename (str, file): Either the full path to the file that should be
           openned and read or an existing open file object.
        start (int, optional): Index of halo in file (relative to the end of the
            header) where read should start. Defaults to 0.
        nhalo (int, optional): Number of halos that should be read. Defaults to
            all halos.
        header_size (int, optional): Size of the header preceeding trees in the
            file. Defaults to 0.
        item_dtype (np.dtype, optional): Data type of each halo entry. Defaults
            to dtype_header_default.

    Returns:
        np.ndarray: Structure array of halo data.

    """
    if header_size is None:
        header_size = 0
    if item_dtype is None:
        item_dtype = dtype_header_default
    item_dtype = np.dtype(item_dtype)
    # Open file as necessary
    opened = False
    if isinstance(filename, str):
        fd = open(filename, 'rb')
        opened = True
    else:
        fd = filename
    # Seek to halo location and read
    offset = header_size + (start * item_dtype.itemsize)
    fd.seek(offset, os.SEEK_SET)
    if nhalo is None:
        nhalo = -1
    out = np.fromfile(fd, dtype=item_dtype, count=nhalo)
    if opened:
        fd.close()
    return out


def _save_to_file(filename, data, start=0, header_size=None):
    r"""Save one or more halos to a file using np.tofile.

    Args:
        filename (str, file): Either the full path to the file that should be
           openned and saved to or an existing open file object.
        data (np.ndarray): Structured array of halo data that should be saved.
        start (int, optional): Index in file (in halso) where halos should be
            written. Defaults to 0.
        header_size (int, optional): Size of the header preceeding trees in the
            file. Defaults to 0.

    """
    if header_size is None:
        header_size = 0
    item_dtype = data.dtype
    # Open file as necessary
    opened = False
    if isinstance(filename, str):
        fd = open(filename, 'rb+')
        opened = True
    else:
        fd = filename
    # Seek to halo location and write
    offset = header_size + (start * item_dtype.itemsize)
    fd.seek(offset, os.SEEK_SET)
    data.tofile(fd)
    if opened:
        fd.close()


def read_trees_default(filename, **kwargs):
    r"""Read trees from a file.

    Args:
        filename (str, np.memmap): Either the full path to the file that should
            be read via memmap or an existing memmapped file.
        **kwargs: Additional keyword arguments are passed to _read_from_mmap.

    Returns:
        dict: Arrays of fields for each halo.

    """
    # out_ra = _read_from_file(filename, **kwargs)
    out_ra = _read_from_mmap(filename, **kwargs)
    # if len(out_ra) == 1:
    #     for k in out_ra.dtype.fields.keys():
    #         if not isinstance(out_ra[k], np.ndarray):
    #             print(k, out_ra[k])
    #             raise Exception
    #     out = {k: out_ra[k].copy() for k in out_ra.dtype.fields.keys()}
    # else:
    out = {k: out_ra[k].copy() for k in out_ra.dtype.fields.keys()}
    return out


def save_trees_default(filename, data, item_dtype=None, **kwargs):
    r"""Save trees to a file.

    Args:
        filename (str, np.memmap): Either the full path to the file that should
            be saved to via memmap or an existing memmapped file.
        data (dict): Arrays of fields for each halo.
        item_dtype (np.dtype, optional): Data type of each halo entry. Defaults
            to dtype_header_default.
        **kwargs: Additional keyword arguments are passed to _save_to_mmap.

    """
    if item_dtype is None:
        item_dtype = dtype_header_default
    item_dtype = np.dtype(item_dtype)
    nhalo = len(data[next(iter(data))])  # Gross, but Py 2 & 3 compat
    data_ra = np.empty(nhalo, dtype=item_dtype)
    for k in item_dtype.fields.keys():
        data_ra[k] = data[k]
    # return _save_to_file(filename, data_ra, **kwargs)
    return _save_to_mmap(filename, data_ra, **kwargs)


class LHaloTreeReader:
    r"""Class for reading halos from an LHaloTree file.

    Args:
        filename (str): Full path to file that trees should be read from.
        parameters (dict, optional): Dictionary of simulation parameters. If not
            provided, parameters are loaded from parameter_file.
        parameter_file (str, optional): Full path to file that contains
            simulation parameters. If not provided, one with the suffix '.param'
            is searched for in the same directory as the tree file. An IOError
            will be raised if it cannot be found.
        scale_factors (list or np.ndarray, optional): 1D array of scale factors for each
            snapshot. If not provided, they are loaded from scale_factor_file.
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
        validate (bool, optional): If True, the data in the file will be
            validated and errors will be raised if there are inconsistencies.
            Defaults to False.

    Attributes:
        filename (str): Full path to file that trees should be read from.
        fileindex (int): Index of this file in the full set of trees.
        filepattern (str): Glob style pattern that can be used to find other
            files in the full set of trees.
        parameter_file (str): Full path to file that contains simulation
            parameters.
        header_size (int): The size of the file header.
        nhalos_per_tree (np.ndarray): The number of halos in each of the ntree
            trees in the file.
        nhalos_before_tree (np.ndarray): The number of halos before each of the
            ntree trees in the file.
        totnhalos (int): Total number of halos in this file.
        ntrees (int): Number of trees in this file.
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

    def __init__(self, filename, parameters=None, parameter_file=None,
                 scale_factors=None, scale_factor_file=None,
                 header_size=None, nhalos_per_tree=None, read_header_func=None,
                 item_dtype=None, silent=False, validate=False):
        # Files
        self.filename = self._verify_file(filename)
        self.fileindex = 0
        self.filepattern = self.filename
        ext = self.filename.split('.')[-1]
        if ext.isdigit():
            self.fileindex = int(ext)
            self.filepattern = os.path.splitext(self.filename)[0] + ".*"
        if parameters is not None:
            self._parameters = parameters
            self.parameter_file = None
        else:
            self.parameter_file = self._verify_file(
                parameter_file, suffix='.param', error_tag='Parameter file',
                silent=silent)
            self._parameters = None
        if scale_factors is not None:
            self._scale_factors = np.asarray(scale_factors)
            self.scale_factor_file = None
        else:
            self.scale_factor_file = self._verify_file(
                scale_factor_file, suffix='.a_list', error_tag='Scale factor file',
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
        self.nhalos_before_tree = (np.cumsum(self.nhalos_per_tree) -
                                   self.nhalos_per_tree)
        self.totnhalos = np.sum(self.nhalos_per_tree)
        self.ntrees = len(self.nhalos_per_tree)
        self.item_dtype = np.dtype(item_dtype)
        # Fields
        self.raw_fields = list(self.item_dtype.fields.keys())
        self.add_fields = ['desc_uid', 'scale_factor', 'uid',
                           'x', 'y', 'z', 'vx', 'vy', 'vz',
                           'Jx', 'Jy', 'Jz']
        self.fields = self.raw_fields + self.add_fields
        for k in ['Pos', 'Vel', 'Spin']:
            self.fields.remove(k)
        # Check file size
        item_size = self.item_dtype.itemsize
        body_size = self.totnhalos * item_size
        file_size = os.stat(self.filename).st_size
        if body_size != (file_size - self.header_size):  # pragma: no cover
            raise IOError(
                f"File is {file_size} bytes, but {self.totnhalos} items of size "
                f"{item_size} with header of {self.header_size} bytes should be "
                f"{body_size + self.header_size} bytes total.")
        # Load all data, validate, and cache some fields
        self.set_global_properties(validate=validate)

    def set_global_properties(self, validate=False):
        r"""Set attributes for all trees by loading all of the halos.

        Args:
            validate (bool, optional): If True, the data loaded from the
                file will be validated. Defaults to False.

        .. todo:: For small files, the data could be cached which would
                  greatly speed up loading.

        """
        # Tree num array
        self.treenum_arr = np.zeros(self.totnhalos, dtype='int64')
        start = self.nhalos_before_tree
        stop = start + self.nhalos_per_tree
        for t in range(self.ntrees):
            self.treenum_arr[start[t]:stop[t]] = t
        # Memmap/file object
        self.fobj = np.memmap(self.filename, dtype=self.item_dtype, mode='c',
                              offset=self.header_size)
        # Read all data
        data = self.read_all_trees(skip_add_fields=True, validate=validate)
        # File number
        self.filenum = data['FileNr'][0]
        if (data['SnapNum'][0] + 1) != len(self.scale_factors):  # pragma: no cover
            ytreeLogger.warning(
                f"First FoF central is in snapshot {data['SnapNum'][0] + 1}/{len(self.scale_factors)}.")
        # Halo unique IDs
        self.all_uids = np.bitwise_or(
            np.int64(self.filenum) << 32, np.arange(self.totnhalos, dtype='int64'))
        # Get descendant unique IDs
        desc = data['Descendant']
        pos_flag = (desc >= 0)
        desc_uid = np.zeros(self.totnhalos, dtype='int64') - 1
        desc_abs = self.get_total_index(self.treenum_arr, desc)
        desc_uid[pos_flag] = self.all_uids[desc_abs[pos_flag]]
        self.all_desc_uids = desc_uid
        # Add fields and cache root fields
        data = self.add_computed_fields(-1, data, validate=validate)
        root_idx = self.nhalos_before_tree
        self._root_data = dict()
        for k in self.fields:
            self._root_data[k] = data[k][root_idx]

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
            if suffix is None:  # pragma: no cover
                raise IOError(f"{error_tag} dosn't exist: {filename}")
            pattern = os.path.join(os.path.dirname(self.filename), '*' + suffix)
            files = glob.glob(pattern)
            if len(files) == 0:  # pragma: no cover
                raise IOError(f"{error_tag} could not be located matching: {pattern}")
            else:
                filename = files[0]
                if not silent:
                    print(f"Using {error_tag.lower()} found at {filename}")
        return filename

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
        u_cms = float(self.parameters['UnitVelocity_in_cm_per_s'])
        out = f"{u_cms / 100000.0:f}*km/s"
        # TODO: Does this need adjusted for comoving?
        return out

    @property
    def units_len(self):
        r"""str: Units of length."""
        u_cm = float(self.parameters['UnitLength_in_cm'])
        out = f"{u_cm / 3.085678e+21:f}*kpc"
        if self.comoving:
            out += "/h"
        return out

    @property
    def units_mass(self):
        r"""str: Units of mass."""
        u_g = float(self.parameters['UnitMass_in_g'])
        out = f"{u_g / 1.989e+33:f}*Msun"
        if self.comoving:
            out += "/h"
        return out

    @property
    def scale_factors(self):
        r"""np.ndarray: Array of scale factors at each snapshot."""
        if self._scale_factors is None:
            self._scale_factors = np.fromfile(self.scale_factor_file, sep='\n')
        return self._scale_factors

    def get_total_index(self, treenum, halonum=None):
        r"""Get the slice that selects halos in a single tree.

        Args:
            treenum (int, np.ndarray): Index/indicies of tree(s) to get the
                total index for If -1, a slice that includes all halos in the
                file will be returned.
            halonum (int, np.ndarray, optional): Index/indices of halo(s) within
                the tree(s) to get the total index for in the file. Defaults to
                None and the slice for the entire tree is returned.

        Returns:
            slice, int: Slice/indices of halo(s) for this tree/halo(s).

        """
        if (not isinstance(treenum, np.ndarray)) and (treenum == -1):
            return slice(0, self.totnhalos)
        start = self.nhalos_before_tree[treenum]
        if halonum is None:
            return slice(start, start + self.nhalos_per_tree[treenum])
        else:
            return start + halonum

    # def get_tree_offset(self, treenum):
    #     r"""Get the offset in bytes of a tree from the beginning of the file.

    #     Args:
    #         treenum (int): Index of the tree to compute the offset of.

    #     Returns:
    #         int: Number of bytes from beginning of the file to the start of the
    #             requested tree.

    #     """
    #     if treenum == -1:
    #         return self.header_size
    #     offset = self.header_size + (self.nhalos_before_tree[treenum] *
    #                                  self.item_dtype.itemsize)
    #     return offset

    # def get_halo_offset(self, treenum, halonum):
    #     r"""Get the offset in bytes of a halo from the beginning of the file.

    #     Args:
    #         treenum (int): Index of the tree that requested halo is in.
    #         halonum (int): Index of the requested in halo in the tree.

    #     Returns:
    #         int: Number of bytes from beginning of the file to the start of the
    #             requested halo.

    #     """
    #     offset = self.get_tree_offset(treenum)
    #     if halonum is not None:
    #         offset += halonum * self.item_dtype.itemsize
    #     return offset

    def read_single_tree(self, treenum, halonum=None, fd=None,
                         skip_add_fields=False, validate=False):
        r"""Read a single tree from the file.

        Args:
            treenum (int): Index of the tree that should be returned. If -1,
                data for every tree in the file will be returned.
            halonum (int, optional): If provided, this is the index of a
                particular halo within the tree that should be returned. If not
                provided, the entire tree is returned.
            fd (file, optional): Open file identifier. If not provided, the file
                is opened for the read and then closed.
            skip_add_fields (bool, optional): If True, the calculated fields
                will not be added or checked for. Defaults to False.
            validate (bool, optional): If True, the resulting data will be
                validated. Defaults to False.

        Returns:
            dict: Dictionary of fields for each halo in the file/tree/halo.

        """
        if treenum >= 0:
            start = self.nhalos_before_tree[treenum]
            if halonum is None:
                nhalo = self.nhalos_per_tree[treenum]
            else:
                nhalo = 1
        else:
            start = 0
            nhalo = self.totnhalos
        # Read from map/file
        out = read_trees_default(self.fobj, start=start, nhalo=nhalo)
        # Validate
        if validate:
            self.validate_tree(treenum, out, halonum=halonum)
        # Add fields
        if not skip_add_fields:
            out = self.add_computed_fields(treenum, out, halonum=halonum,
                                           validate=validate)
        return out

    def read_single_halo(self, treenum, halonum, **kwargs):
        r"""Read a single halo entry from a tree in the file.

        Args:
            treenum (int): Index of the tree that contains the requested halo.
            halonum (int): Index of the halo within its tree.
            **kwargs: Additional keyword arguments are passed to
                read_single_tree.

        Returns:
            np.ndarray, dict: Dictionary or single element structured array with
                fields for the corresponding halo.

        """
        return self.read_single_tree(treenum, halonum=halonum, **kwargs)

    def read_single_root(self, treenum, **kwargs):
        r"""Read an entry for a single tree root. First check to see if the root
        was chached.

        Args:
            treenum (int): Index of the tree that data should be returned for.
                If -1, the data for every root in the file is returned.
            **kwargs: Additional keyword arguments are passed to
                read_single_tree in the event that the root data is not cached.

        Returns:
            np.ndarray, dict: Dictionary or single element structured array with
                fields for the corresponding root.

        """
        root_data = self._root_data
        if treenum == -1:
            return root_data
        out = dict()
        for k, v in root_data.items():
            out[k] = np.array([v[treenum]], dtype=v.dtype)
        return out

    def read_all_trees(self, **kwargs):
        r"""Read a all lhalotrees from the file.

        Args:
            **kwargs: All keyword arguments are passed to read_single_tree.

        Returns:
            dict, np.ndarray: Dictionary or structured array with fields for
                each halo in the file.

        """
        return self.read_single_tree(-1, halonum=None, **kwargs)

    def add_computed_fields(self, treenum, tree, halonum=None, validate=False):
        r"""Add computed fields to the numpy array.

        Args:
            treenum (int): Index of tree in file.
            tree (dict): Dictionary of fields for each halo in the tree.
            halonum (int, optional): Index of halo in the tree if tree contains
                a single halo.
            validate (bool, optional): If True, the resulting data will be
                validated. Defaults to False.

        Returns:
            dict: Dictionary of fields for each halo with added fields.

        """
        nhalos = len(tree['SnapNum'])
        if treenum == -1:
            assert(nhalos == self.totnhalos)
            assert(halonum is None)
        elif nhalos != self.nhalos_per_tree[treenum]:
            assert(nhalos == 1)
            assert(halonum is not None)
        else:
            halonum = None
        # Unique ID for each halo and descendant in tree
        idx = self.get_total_index(treenum, halonum)
        uid = self.all_uids[idx]
        desc_uid = self.all_desc_uids[idx]
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
        # Spin x, y, z
        Jx = tree['Spin'][:, 0]
        Jy = tree['Spin'][:, 1]
        Jz = tree['Spin'][:, 2]
        # Add new fields
        new_fields = dict(uid=uid, desc_uid=desc_uid, scale_factor=scale_factor,
                          x=x, y=y, z=z, vx=vx, vy=vy, vz=vz, Jx=Jx, Jy=Jy, Jz=Jz)
        out = tree
        out.update(**new_fields)
        if validate:
            self.validate_fields(out)
        return out

    def validate_tree(self, treenum, tree, halonum=None):
        r"""Check that the tree conforms to expectation.

        Args:
            treenum (int): Index of the tree being validated in the file.
            tree (dict): Dictionary of fields for each halo in the tree.
            halonum (int): Index of halo in tree if this is a single halo.
                Defaults to None and tree is treated as a complete tree.

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
        if treenum == -1:
            nhalos = self.totnhalos
            halonum = None
        else:
            if halonum is not None:
                nhalos = 1
            else:
                nhalos = self.nhalos_per_tree[treenum]
        fields = list(tree.keys())
        for k in fields:
            assert(len(tree[k]) == nhalos)
        # Check fields
        for k in self.raw_fields:
            assert(k in fields)
        # Don't check tree indices for a single halo
        if halonum is not None:
            return
        # For all trees get list of local nhalos for every halo
        if treenum == -1:
            treenum_arr = self.treenum_arr
            nhalos = self.nhalos_per_tree[treenum_arr]
        # Check that halos are within tree
        for k in halo_fields:
            assert((tree[k] < nhalos).all())
        # Check FOF central exists and all subs in one snapshot
        central = tree['FirstHaloInFOFgroup']
        assert((central >= 0).all())
        if treenum == -1:
            central = self.get_total_index(treenum_arr, central)
        assert((tree['SnapNum'] == tree['SnapNum'][central]).all())
        # Check that progenitors/descendants are back/forward in time
        descend = tree['Descendant'].astype('i4')
        has_descend = (descend >= 0)
        not_descend = np.logical_not(has_descend)
        # Not strictly True
        # assert((tree['SnapNum'][not_descend] ==
        #         (len(self.scale_factors) - 1)).all())
        if treenum == -1:
            descend = self.get_total_index(treenum_arr, descend)
        assert((tree['SnapNum'][descend[has_descend]] >
                tree['SnapNum'][has_descend]).all())
        # Check progenitors are back in time
        descend[not_descend] = np.where(not_descend)[0]
        progen1 = tree['FirstProgenitor']
        progen2 = tree['NextProgenitor']
        has_progen1 = (progen1 >= 0)
        has_progen2 = (progen2 >= 0)
        if treenum == -1:
            progen1 = self.get_total_index(treenum_arr, progen1)
            progen2 = self.get_total_index(treenum_arr, progen2)
        assert((tree['SnapNum'][progen1[has_progen1]] <=
                tree['SnapNum'][descend[has_progen1]]).all())
        assert((tree['SnapNum'][progen2[has_progen2]] <=
                tree['SnapNum'][descend[has_progen2]]).all())

    def validate_fields(self, tree):
        r"""Check that the tree/halo has all of the expected fields.

        Args:
            tree (dict): Dictionary of fields for each halo in the tree.

        Raises:
            AssertionError: If the tree does not have all of the expected fields.

        """
        # Check fields
        fields = list(tree.keys())
        for k in self.fields:
            assert(k in fields)
