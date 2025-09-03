#!/usr/bin/env python3
import os
import re


def get_version():
    fn = os.path.join(os.path.dirname(__file__), "..", "ytree", "__init__.py")
    lines = open(fn, mode="r").readlines()
    for line in lines:
        match = re.search(r"__version__\s+=\s+\"(.+)\"", line)
        if match:
            version = match.groups()[0]
            return version


if __name__ == "__main__":
    print(get_version())
