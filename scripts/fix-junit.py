"""
Alter the xml file produced by pytest so the file attribute
reflects the script file and not the file of the base class.
"""

import os
import sys
import xml.etree.ElementTree as ET

if __name__ == "__main__":
    ifn = sys.argv[1]
    print(f"Reading {ifn}.")
    tree = ET.parse(ifn)
    root = tree.getroot()

    for child in root[0]:
        fn = child.attrib["file"]
        if fn.startswith("tests"):
            continue

        cln = child.attrib["classname"]
        fnew = os.path.join(*cln.split(".")[:-1]) + ".py"
        print(f"Changing {fn} to {fnew}.")
        child.attrib["file"] = fnew

    print(f"Writing {ifn}.")
    tree.write(ifn)
