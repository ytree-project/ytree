"""
ConsistentTreesArbor class and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) 2016-2017, Britton Smith <brittonsmith@gmail.com>
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import numpy as np

from yt.funcs import \
    get_pbar
from yt.units.yt_array import \
    UnitParseError

from ytree.arbor.arbor import \
    MonolithArbor
from ytree.arbor.tree_node import \
    TreeNode

class ConsistentTreesArbor(MonolithArbor):
    """
    Class for Arbors from consistent-trees output files.
    """

    def _read_fields(self, root_node, fields, dtypes=None,
                     f=None, root_only=False):
        if dtypes is None:
            dtypes = {}

        close = False
        if f is None:
            close = True
            f = open(self.filename, "r")
        f.seek(root_node._si)
        if root_only:
            data = [f.readline()]
        else:
            data = f.read(
                root_node._ei -
                root_node._si).split("\n")
        if close:
            f.close()

        nhalos = len(data)
        field_data = {}
        fi = self.field_info
        for field in fields:
            field_data[field] = \
              np.empty(nhalos, dtype=dtypes.get(field, float))

        for i, datum in enumerate(data):
            ldata = datum.strip().split()
            for field in fields:
                dtype = dtypes.get(field, float)
                field_data[field][i] = dtype(ldata[fi[field]["column"]])

        for field in fields:
            units = fi[field].get("units", "")
            if units != "":
                field_data[field] = self.arr(field_data[field], units)

        return field_data

    def _grow_tree(self, root_node, fields=None, f=None):
        if fields is None:
            fields = []
        else:
            fields = fields.copy()
        for field in ["id", "desc_id"]:
            if field not in fields:
                fields.append(field)

        idtype  = np.int64
        dtypes  = {"id": idtype, "desc_id": idtype}
        field_data = self._read_fields(root_node, fields,
                                       dtypes=dtypes)
        uids    = field_data.pop("id")
        descids = field_data.pop("desc_id")
        nhalos  = uids.size
        nodes   = np.empty(nhalos, dtype=np.object)
        uidmap  = {}
        for i in range(nhalos):
            nodes[i] = TreeNode(uids[i], arbor=self)

        # replace first halo with the root node
        root_node.uids    = uids
        root_node.descids = descids
        root_node.nodes   = nodes
        nodes[0]          = root_node
        for i, node in enumerate(nodes):
            node.treeid = i
            node.root = root_node
            descid = descids[i]
            uidmap[uids[i]] = i
            if descid != -1:
                desc = nodes[uidmap[descids[i]]]
                desc.add_ancestor(node)
                node.descendent = desc

        self._store_fields(root_node, field_data, root_only=False)

    def _set_default_selector(self):
        """
        Mass is "mvir".
        """
        self.set_selector("max_field_value", "Mvir")

    def _parse_parameter_file(self):
        """
        Read all relevant parameters from file header and
        modify unit registry for hubble constant.
        """

        self._field_data = {}
        fields = []
        fi = {}
        fdb = {}
        rems = ["%s%s%s" % (s[0], t, s[1])
                for s in [("(", ")"), ("", "")]
                for t in ["comoving", "physical"]]

        f = open(self.filename, "r")
        # Read the first line as a list of all fields.
        # Do some footwork to remove awkard characters.
        rfl = f.readline()[1:].strip().split()
        for pf in rfl:
            if "(" in pf and ")" in pf:
                bt = pf[pf.find("(")+1:pf.rfind(")")]
                if bt.isdigit():
                    fields.append(pf[:pf.find("(")])
                else:
                    fields.append(pf)
            else:
                fields.append(pf)

        # Now grab a bunch of things from the header.
        while True:
            line = f.readline()
            if line is None:
                raise IOError(
                    "Encountered enexpected EOF reading %s." %
                    self.filename)
            elif not line.startswith("#"):
                self._ntrees = int(line.strip())
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
                tfields, desc = line[1:].strip().split(":", maxsplit=1)
                for sep in ["/", ","]:
                    if sep in tfields:
                        tfields = tfields.split(sep)
                if not isinstance(tfields, list):
                    tfields = [tfields]
                for tfield in tfields:
                    punits = ""
                    fdb[tfield.lower()] = {"description": desc.strip()}
                    if "(" in line and ")" in line:
                        punits = desc[desc.find("(")+1:desc.rfind(")")]
                        for rem in rems:
                            while rem in punits:
                                pre, mid, pos = punits.partition(rem)
                                punits = pre + pos
                        try:
                            x = self.quan(1, punits)
                        except UnitParseError:
                            punits = ""
                        fdb[tfield.lower()]["units"] = punits
        self._hoffset = f.tell()
        f.close()

        # Fill the field info with the units found above.
        for i, field in enumerate(fields):
            if "(" in field and ")" in field:
                cfield = field[:field.find("(")]
            else:
                cfield = field
            fi[field] = fdb.get(field.lower(),
                                {"description": "",
                                 "units": ""})
            fi[field]["column"] = i
        self.field_list = fields
        self.field_info = fi

        self.box_size = self.quan(float(box[0]), box[1])

    def _plant_trees(self):
        """
        Create the list of root tree nodes.
        """

        lkey = len("tree ")+1
        block_size = 32768

        f = open(self.filename, "r")
        file_size = f.seek(0, 2)
        pbar = get_pbar("Loading tree roots", file_size)
        f.seek(self._hoffset)
        self._trees = np.empty(self._ntrees, dtype=np.object)

        offset = self._hoffset
        itree = 0
        nblocks = np.ceil(float(file_size) /
                          block_size).astype(np.int64)
        for ib in range(nblocks):
            my_block = min(block_size, file_size - offset)
            buff = f.read(my_block)
            lihash = -1
            for ih in range(buff.count("#")):
                ihash = buff.find("#", lihash+1)
                inl = buff.find("\n", ihash+1)
                if inl < 0:
                    buff += f.readline()
                    inl = len(buff)
                uid = int(buff[ihash+lkey:inl])
                lihash = ihash
                my_node = TreeNode(uid, arbor=self)
                my_node.root = -1
                my_node._root_field_data = {}
                my_node._tree_field_data = {}
                my_node._si = offset + inl + 1
                self._trees[itree] = my_node
                if itree > 0:
                    self._trees[itree-1]._ei = offset + ihash - 1
                itree += 1
            offset = f.tell()
            pbar.update(offset)
        self._trees[-1]._ei = offset
        f.close()
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
