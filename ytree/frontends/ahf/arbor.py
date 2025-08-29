"""
AHFArbor class and member functions



"""

# -----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------

from collections import defaultdict
import glob
import os
import re

from ytree.data_structures.arbor import CatalogArbor
from ytree.frontends.ahf.fields import AHFFieldInfo, AHFCRMFieldInfo
from ytree.frontends.ahf.io import AHFDataFile, AHFCRMDataFile
from ytree.frontends.ahf.misc import parse_AHF_file
from unyt.unit_registry import UnitRegistry
from ytree.utilities.io import f_text_block


class AHFArbor(CatalogArbor):
    """
    Arbor for Amiga Halo Finder data without a CRMratio2 file.

    In this instance, we will use the mtree files to assemble the tree.
    """

    _ahf_prefix = None
    _mtree_prefix = None
    _data_suffix = ".AHF_halos"
    _mtree_suffix = ".AHF_mtree"
    _par_suffix = ".parameter"
    _crm_prefix = "MergerTree_"
    _crm_suffix = "-CRMratio2"
    crm_filename = None
    _frequent_crm_midfixes = (".txt", "")
    _field_info_class = AHFFieldInfo
    _data_file_class = AHFDataFile

    def __init__(
        self,
        filename,
        log_filename=None,
        parameter_filename=None,
        crm_filename=None,
        hubble_constant=1.0,
        box_size=None,
        omega_matter=None,
        omega_lambda=None,
        name_config=None,
    ):
        self.unit_registry = UnitRegistry()
        self.hubble_constant = hubble_constant
        self.omega_matter = omega_matter
        self.omega_lambda = omega_lambda
        self._box_size_user = box_size

        self.log_filename = log_filename
        self.parameter_filename = parameter_filename
        self.crm_filename = crm_filename

        if name_config is None:
            name_config = {}
        self._set_naming_conventions(name_config)

        self._file_pattern = re.compile(
            rf"(^.+[^0-9a-zA-Z]+)(\d+).*{self._par_suffix}$"
        )
        super().__init__(filename)

    def _set_naming_conventions(self, config):
        """
        Set some filename conventions.
        """

        for k, v in config.items():
            if not re.match(r"\w+_(?:prefix|suffix)", k):
                raise ValueError(
                    f'name_config entry must end in either prefix or suffix: "{k}"'
                )
            if not hasattr(self, f"_{k}"):
                raise ValueError(
                    f'name_config entry not associated with a known attribute: "{k}"'
                )

            setattr(self, f"_{k}", v)

    @classmethod
    def _is_crm_file(cls, filename):
        """
        Checking if this has the proper crm prefix and suffix.
        """

        return os.path.basename(filename).startswith(
            cls._crm_prefix
        ) and filename.endswith(cls._crm_suffix)

    def _guess_crm_filename(self, filename):
        """
        Take an educated guess at the crm filename.

        Return None if our guess does not exist.
        """

        if self.crm_filename is not None:
            if os.path.exists(self.crm_filename):
                return self.crm_filename
            else:
                return None

        if AHFArbor._is_crm_file(filename):
            if os.path.exists(filename):
                return filename
            else:
                return None

        # Searching for <keyword>.something.<suffix>
        res = re.search(rf"([^\.]+)\.[^\.]+{self._par_suffix}$", filename)
        if not res:
            return None

        filekey = res.groups()[0]
        ddir = os.path.dirname(filekey)

        for midfix in self._frequent_crm_midfixes:
            bname = os.path.basename(filekey) + midfix
            fname = os.path.join(ddir, f"{self._crm_prefix}{bname}{self._crm_suffix}")
            if os.path.exists(fname):
                return fname

        return None

    @classmethod
    def _is_parameter_file(cls, filename):
        """
        Check if file has the proper suffix.
        """

        return filename.endswith(cls._par_suffix)

    def _parse_parameter_file(self):
        df = AHFDataFile(self.parameter_filename, self)

        pars = {
            "simu.omega0": "omega_matter",
            "simu.lambda0": "omega_lambda",
            "simu.boxsize": "box_size",
        }

        if self.log_filename is None:
            fns = glob.glob(df.filekey + "*.log")
            if fns:
                log_filename = fns[0]
            else:
                log_filename = None
        else:
            log_filename = self.log_filename

        if log_filename is not None and os.path.exists(log_filename):
            vals = parse_AHF_file(log_filename, pars, sep=":")
            for attr in ["omega_matter", "omega_lambda"]:
                setattr(self, attr, vals.get(attr))
            if "box_size" in vals:
                self.box_size = self.quan(vals["box_size"], "Mpc/h")

        if self._box_size_user is not None:
            self.box_size = self.quan(self._box_size_user, "Mpc/h")

        # fields from from the .AHF_halos files
        f = open(f"{df.data_filekey}{self._data_suffix}")
        line = f.readline()
        f.close()

        fields = [key[: key.rfind("(")] for key in line[1:].strip().split()]
        fi = dict(
            [(field, {"column": i, "file": "halos"}) for i, field in enumerate(fields)]
        )

        # the scale factor comes from the catalog file header
        fields.append("redshift")
        fi["redshift"] = {"file": "header", "units": ""}

        # the descendent ids come from the .AHF_mtree files
        fields.append("desc_id")
        fi["desc_id"] = {"file": "mtree", "units": ""}

        self.field_list = fields
        self.field_info.update(fi)

    _fprefix = None

    @property
    def _prefix(self):
        if self._fprefix is None:
            # Match a patten of any characters, followed by some sort of
            # separator (e.g., "." or "_"), then a number, and eventually
            # the suffix.
            reg = self._file_pattern.search(self.parameter_filename)
            self._fprefix = reg.groups()[0]
        return self._fprefix

    def _get_data_files(self):
        """
        Get all *.parameter files and sort them in reverse order.
        """
        my_files = glob.glob(f"{self._prefix}*{self._par_suffix}")
        # sort by catalog number
        my_files.sort(key=self._get_file_index)
        self.data_files = [self._data_file_class(f, self) for f in my_files]

        # Set the mtree file for file i to that of i-1, since
        # AHF thinks in terms of progenitors and not descendents.
        for i, data_file in enumerate(self.data_files[:-1]):
            data_file.mtree_filename = self.data_files[i + 1].mtree_filename
        self.data_files[-1].mtree_filename = None
        self.data_files.reverse()

    def _get_file_index(self, f):
        reg = self._file_pattern.search(f)
        if not reg:
            raise RuntimeError(f"Could not locate index within file: {f}.")
        return int(reg.groups()[1])

    @classmethod
    def _is_valid(self, *args, **kwargs):
        """
        File must end in .parameter.
        """
        fn = args[0]
        if not AHFArbor._is_parameter_file(fn):
            return False

        if "crm_filename" in kwargs:
            return False

        if self._guess_crm_filename(self, fn) is not None:
            return False

        return True


class AHFCRMArbor(AHFArbor):
    """
    Arbor for AHF data that includes a CRM file.

    The CRM file contains all the halo links, so we don't have to
    assemble them from the mtree files.
    """

    _has_uids = True
    _field_info_class = AHFCRMFieldInfo
    _data_file_class = AHFCRMDataFile

    def _set_paths(self, filename):
        """
        Get both a CRM file and a parameter file.

        Raise an exception if we can't get both.
        """

        super()._set_paths(filename)

        if self.crm_filename is None:
            self.crm_filename = self._guess_crm_filename(filename)
        else:
            if not os.path.exists(self.crm_filename):
                raise RuntimeError(
                    "Specified crm_filename does not exist: ", self.crm_filename
                )

        if self.crm_filename is None:
            raise RuntimeError(
                f"crm_filename is None for {type(self)}. This shouldn't be."
            )

        if self.parameter_filename is None:
            self.parameter_filename = self._guess_parameter_filename(filename)
        else:
            if not os.path.exists(self.parameter_filename):
                raise RuntimeError(
                    "Specified parameter_filename does not exist: ",
                    self.parameter_filename,
                )

        if self.parameter_filename is None:
            raise RuntimeError(
                f"parameter_filename is None for {type(self)}. This shouldn't be."
            )

    def _set_parameter_filename(self, filename):
        """
        We have a whole thing here...
        """

        pass

    def _guess_parameter_filename(self, filename):
        """
        Guess parameter filename from the crm filename.
        """

        if self.parameter_filename is not None:
            if os.path.exists(self.parameter_filename):
                return self.parameter_filename
            else:
                return None

        basename = os.path.basename(filename)
        filekey = basename[len(self._crm_prefix) : -len(self._crm_suffix)]

        # try a couple guesses at naming conventions,
        # but don't work too hard.
        for midfix in self._frequent_crm_midfixes:
            pfns = glob.glob(
                os.path.join(self.directory, filekey[: -len(midfix)])
                + f"*{self._par_suffix}"
            )
            if pfns:
                break

        # just look for all files with the right suffix and hope for the best
        if not pfns:
            pfns = glob.glob(f"*{self._par_suffix}")

        if not pfns:
            raise RuntimeError(
                f"Could not find any files ending in {self._par_suffix} "
                "from which to get parameters. Put some of those in here."
            )

        try:
            pfns.sort(key=self._get_file_index)
            return pfns[-1]

        except Exception:
            return None

    def _plant_trees(self):
        if self.is_planted:
            return

        self._compute_links()
        super()._plant_trees()

    def _compute_links(self):
        """
        Read the CRMratio2 file and hand out a dictionary of
        uid: desc_uid for each data file.
        """

        links = defaultdict(dict)

        f = open(self.crm_filename, mode="r")
        for i in range(3):
            f.readline()

        for line, loc in f_text_block(f, pbar_string="Computing links"):
            if line.startswith("END"):
                break

            online = line.split()
            thing = online[0]
            if len(online) == 2:
                my_descid = int(thing)
                continue

            my_id = int(thing)
            cid = int(thing[:-12])
            links[cid][my_id] = my_descid
        f.close()

        for df in self.data_files:
            df._links = links[df._catalog_index]

    @classmethod
    def _is_valid(self, *args, **kwargs):
        """
        Filename must end in .parameter or match the CRM naming
        convention.
        """
        fn = args[0]
        # if it is a crm file, then we are good to go
        if AHFCRMArbor._is_crm_file(fn):
            return True

        # if it is not a parameter file, then it can't be of this type
        if not AHFCRMArbor._is_parameter_file(fn):
            return False

        mtree_fn = self._guess_crm_filename(self, fn)
        if mtree_fn is None or not os.path.exists(mtree_fn):
            return False

        return True
