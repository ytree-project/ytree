"""
ConsistentTreesArbor class and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import numpy as np
import re
import operator
import os

from yt.funcs import \
    get_pbar
from yt.data_objects.data_containers import \
    UnitParseError

from ytree.data_structures.arbor import \
    Arbor
from ytree.data_structures.tree_node import \
    TreeNode

from ytree.frontends.consistent_trees.fields import \
    ConsistentTreesFieldInfo
from ytree.frontends.consistent_trees.io import \
    ConsistentTreesDataFile, \
    ConsistentTreesTreeFieldIO

from ytree.utilities.exceptions import \
    ArborParameterFileEmpty
from ytree.utilities.io import \
    f_text_block

class ConsistentTreesArbor(Arbor):
    """
    Arbors loaded from consistent-trees tree_*.dat files.
    """

    _parameter_file_is_data_file = True
    _field_info_class = ConsistentTreesFieldInfo
    _tree_field_io_class = ConsistentTreesTreeFieldIO

    def _node_io_loop_prepare(self, root_nodes):
        return self._node_io.data_files, [root_nodes]

    def _node_io_loop_start(self, data_file):
        data_file.open()

    def _node_io_loop_finish(self, data_file):
        data_file.close()

    def _get_data_files(self):
        self._node_io.data_files = \
          [ConsistentTreesDataFile(self.filename)]

    def _parse_parameter_file(self, filename=None):
        fields = []
        fi = {}
        fdb = {}
        rems = ["%s%s%s" % (s[0], t, s[1])
                for s in [("(", ")"), ("", "")]
                for t in ["physical, peculiar",
                          "comoving", "physical"]]

        if filename is None:
            filename = self.filename

        f = open(filename, "r")
        # Read the first line as a list of all fields.
        # Do some footwork to remove awkard characters.
        rfl = f.readline()[1:].strip().split()
        reg = re.compile(r"\(\d+\)$")
        for pf in rfl:
            match = reg.search(pf)
            if match is None:
                fields.append(pf)
            else:
                fields.append(pf[:match.start()])

        # Now grab a bunch of things from the header.
        while True:
            line = f.readline()
            if line is None:
                raise IOError(
                    "Encountered enexpected EOF reading %s." %
                    self.filename)
            elif not line.startswith("#"):
                if getattr(self, '_parameter_file_is_data_file', False):
                    self._ntrees = int(line.strip())
                    self._hoffset = f.tell()
                break

            # cosmological parameters
            if "Omega_M" in line:
                pars = line[1:].split(";")
                for j, par in enumerate(["omega_matter",
                                         "omega_lambda",
                                         "hubble_constant"]):
                    v = float(pars[j].split(" = ")[1])
                    setattr(self, par, v)

            # box size
            elif "Full box size" in line:
                pars = line.split("=")[1].strip().split()
                box = pars

            # These are lines describing the various fields.
            # Pull them apart and look for units.
            elif ":" in line:
                tfields, desc = line[1:].strip().split(":", 1)

                # Units are enclosed in parentheses.
                # Pull out what's enclosed and remove things like
                # "comoving" and "physical".
                if "(" in line and ")" in line:
                    punits = desc[desc.find("(")+1:desc.rfind(")")]
                    for rem in rems:
                        while rem in punits:
                            pre, mid, pos = punits.partition(rem)
                            punits = pre + pos
                    try:
                        self.quan(1, punits)
                    except UnitParseError:
                        punits = ""
                else:
                    punits = ""

                # Multiple fields together on the same line.
                for sep in ["/", ","]:
                    if sep in tfields:
                        tfields = tfields.split(sep)
                        break
                if not isinstance(tfields, list):
                    tfields = [tfields]

                # Assign units and description.
                for tfield in tfields:
                    fdb[tfield.lower()] = {"description": desc.strip(),
                                           "units": punits}

        f.close()

        # Fill the field info with the units found above.
        for i, field in enumerate(fields):
            if "(" in field and ")" in field:
                cfield = field[:field.find("(")]
            else:
                cfield = field
            fi[field] = fdb.get(cfield.lower(),
                                {"description": "",
                                 "units": ""})
            fi[field]["column"] = i
        self.field_list = fields
        self.field_info.update(fi)
        self.box_size = self.quan(float(box[0]), box[1])

    def _plant_trees(self):
        self._trees = np.empty(self._ntrees, dtype=np.object)
        if self._ntrees == 0:
            return

        lkey = len("tree ")+1
        block_size = 32768

        data_file = self._node_io.data_files[0]

        data_file.open()
        data_file.fh.seek(0, 2)
        file_size = data_file.fh.tell()
        pbar = get_pbar("Loading tree roots", file_size)
        data_file.fh.seek(self._hoffset)

        offset = self._hoffset
        itree = 0
        nblocks = np.ceil(float(file_size-self._hoffset) /
                          block_size).astype(np.int64)
        for ib in range(nblocks):
            my_block = min(block_size, file_size - offset)
            if my_block <= 0: break
            buff = data_file.fh.read(my_block)
            lihash = -1
            for ih in range(buff.count("#")):
                ihash = buff.find("#", lihash+1)
                inl = buff.find("\n", ihash+1)
                if inl < 0:
                    buff += data_file.fh.readline()
                    inl = len(buff)
                uid = int(buff[ihash+lkey:inl])
                lihash = ihash
                my_node = TreeNode(uid, arbor=self, root=True)
                my_node._si = offset + inl + 1
                my_node._fi = 0
                self._trees[itree] = my_node
                if itree > 0:
                    self._trees[itree-1]._ei = offset + ihash - 1
                itree += 1
            offset = data_file.fh.tell()
            pbar.update(offset)
        self._trees[-1]._ei = offset
        data_file.close()
        pbar.finish()

    @classmethod
    def _is_valid(self, *args, **kwargs):
        """
        File should end in .dat and have a line in the header
        with the string, "Consistent Trees".
        """
        fn = args[0]
        if not fn.endswith(".dat"): return False
        with open(fn, "r") as f:
            valid = False
            while True:
                line = f.readline()
                if line is None or not line.startswith("#"):
                    break
                if "Consistent Trees" in line:
                    valid = True
                    break
            if not valid: return False
        return True

class ConsistentTreesGroupArbor(ConsistentTreesArbor):
    """
    Arbors loaded from consistent-trees locations.dat files.
    """

    _parameter_file_is_data_file = False

    def _node_io_loop_prepare(self, root_nodes):
        fi = np.array([node._fi for node in root_nodes])
        ufi = np.unique(fi)
        data_files = [self._node_io.data_files[i] for i in ufi]
        node_list = [root_nodes[fi == i] for i in ufi]
        return data_files, node_list

    def _get_data_files(self):
        pass

    def _parse_parameter_file(self):
        f = open(self.filename, 'r')
        f.readline()
        self._hoffset = f.tell()
        line = f.readline()
        if not line:
            raise ArborParameterFileEmpty(self.filename)

        fn = line.split()[-1]
        super(ConsistentTreesGroupArbor, self)._parse_parameter_file(filename=fn)

    def _plant_trees(self):
        f = open(self.filename, 'r')
        f.seek(self._hoffset)
        ldata = list(map(
            lambda x: [int(x[0]), int(x[1]), int(x[2]), x[3], len(x[0])],
            [line.split() for line, _ in f_text_block(f)]
            ))
        f.close()

        # It's faster to create and sort arrays and then sort ldata
        # for some reason.
        dfns = np.unique([datum[3] for datum in ldata])
        dfns.sort()
        fids = np.array([datum[1] for datum in ldata])
        fids.sort()
        ufids = np.unique(fids)
        ufids.sort()

        # Some data files may be empty and so unlisted.
        # Make sure file ids and names line up.
        data_files = [None]*(ufids.max()+1)
        for i,fid in enumerate(ufids):
            data_files[fid] = dfns[i]
        self._node_io.data_files = \
          [ConsistentTreesDataFile(fn) for fn in data_files
           if fn is not None]

        ldata.sort(key=operator.itemgetter(1, 2))
        ntrees = len(ldata)
        pbar = get_pbar("Loading tree roots", ntrees)
        self._trees = np.empty(ntrees, dtype=np.object)

        # Set end offsets for each tree.
        # We don't get them from the location file.
        lkey = len("tree ")+3 # length of the separation line between trees
        same_file = np.diff(fids, append=fids[-1]+1) == 0

        for i, tdata in enumerate(ldata):
            my_node        = TreeNode(tdata[0], arbor=self, root=True)
            my_node._si    = tdata[2]
            my_node._fi    = tdata[1]
            # Get end index from next tree.
            if same_file[i]:
                my_node._ei = ldata[i+1][2] - lkey - tdata[4]
            self._trees[i] = my_node
            pbar.update(i)
        pbar.finish()

        # Get end index for last trees in files.
        for i in np.where(~same_file)[0]:
            data_file = self._node_io.data_files[fids[i]]
            data_file.open()
            data_file.fh.seek(0, 2)
            self._trees[i]._ei = data_file.fh.tell()
            data_file.close()

    @classmethod
    def _is_valid(self, *args, **kwargs):
        """
        File should end in .dat and have a line in the header
        with the string, "Consistent Trees".
        """
        fn = args[0]
        if not os.path.basename(fn) == 'locations.dat':
            return False
        with open(fn, "r") as f:
            valid = False
            while True:
                line = f.readline()
                if line is None or not line.startswith("#"):
                    break
                if "TreeRootID FileID Offset Filename" in line:
                    valid = True
            if not valid:
                return False
        return True
