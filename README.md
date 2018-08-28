# ytree

[![Build Status](https://travis-ci.org/brittonsmith/ytree.svg?branch=master)](https://travis-ci.org/brittonsmith/ytree)
[![Coverage Status](https://coveralls.io/repos/github/brittonsmith/ytree/badge.svg)](https://coveralls.io/github/brittonsmith/ytree)
[![Documentation Status](https://readthedocs.org/projects/ytree/badge/?version=latest)](http://ytree.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/ytree.svg)](https://badge.fury.io/py/ytree)
[![DOI](https://zenodo.org/badge/98564214.svg)](https://zenodo.org/badge/latestdoi/98564214)

This is ytree, a [yt](https://github.com/yt-project/yt) extension for generating and working with
merger-tree data.  ytree supports:

 * loading merger-tree data from the Amiga Halo Finder, Consistent-Trees, Rockstar, and LHaloTree formats

 * creating merger trees from Gadget's inline FOF/SUBFIND catalogs

 * fast, on-demand loading of trees and fields

 * symbolic units, derived fields, and alias fields

 * saving trees to a universal format

## Installation

ytree can be installed with pip:

```
pip install ytree
```

To get the development version, clone this repository and install like this:

```
git clone https://github.com/brittonsmith/ytree
cd ytree
pip install -e .
```

## Getting Started

Below is a notebook that demonstrates how to use ytree with merger-tree data.  For
more information, see the full [ytree documenation](https://ytree.readthedocs.io).

 * [Introduction](https://github.com/brittonsmith/ytree/blob/master/doc/source/notebooks/Intro_to_ytree.ipynb)

## Sample Data

Sampled data for all merger-tree formats supported by ytree is available on the
[yt Hub](https://girder.hub.yt/) in the
[ytree data](https://girder.hub.yt/#collection/59835a1ee2a67400016a2cda) collection.

## Contributing

ytree would be much better with your contribution!  As an extension of
[the yt Project](https://yt-project.org/), we follow the yt
[guidelines for contributing](https://github.com/yt-project/yt#contributing).

## Citing ytree


If you use ytree in your work, please cite the following:

```
Britton Smith, & Meagan Lang. (2018, February 16). ytree: merger-tree toolkit. Zenodo.
https://doi.org/10.5281/zenodo.1174374
```

For BibTeX users:

```
  @misc{britton_smith_2018_1174374,
    author       = {Britton Smith and
                    Meagan Lang},
    title        = {ytree: merger-tree toolkit},
    month        = feb,
    year         = 2018,
    doi          = {10.5281/zenodo.1174374},
    url          = {https://doi.org/10.5281/zenodo.1174374}
  }
```

If possible, please also add a footnote pointing to
https://ytree.readthedocs.io.

## Resources

 * The latest documentation can be found at https://ytree.readthedocs.io

 * ytree is an extension of [the yt Project](https://yt-project.org/). The [yt-project community resources](https://github.com/yt-project/yt#resources) can be used for ytree-related communication.
