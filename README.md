# ytree

[![CircleCI](https://circleci.com/gh/ytree-project/ytree/tree/main.svg?style=svg)](https://circleci.com/gh/ytree-project/ytree/tree/main)
[![codecov](https://codecov.io/gh/ytree-project/ytree/branch/main/graph/badge.svg)](https://codecov.io/gh/ytree-project/ytree)
[![Documentation Status](https://readthedocs.org/projects/ytree/badge/?version=latest)](http://ytree.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/ytree.svg)](https://badge.fury.io/py/ytree)
[![DOI](https://joss.theoj.org/papers/10.21105/joss.01881/status.svg)](https://doi.org/10.21105/joss.01881)
[![yt-project](https://img.shields.io/static/v1?label="works%20with"&message="yt"&color="blueviolet")](https://yt-project.org)

This is `ytree`, a [yt](https://github.com/yt-project/yt) extension for
working with merger tree data.

Structure formation in cosmology proceeds in a hierarchical fashion,
where dark matter halos grow via mergers with other halos. This type
of evolution can be conceptualized as a tree, with small branches
connecting to successively larger ones, and finally to the trunk. A
merger tree describes the growth of halos in a cosmological
simulation by linking a halo appearing in a given snapshot to its
direct ancestors in a previous snapshot and its descendent in the next
snapshot.

Merger trees are computationally expensive to generate and a great
number of codes exist for computing them. However, each of these codes
saves the resulting data to a different format. `ytree` is Python
package for reading and working with merger tree data from multiple
formats. If you are already familiar with using
[yt](https://github.com/yt-project/yt) to analyze snapshots from
cosmological simulations, then think of `ytree` as the `yt` of merger
trees.

To load a merger tree data set with `ytree` and print the masses of
all the halos in a single tree, one could do:

```
>>> import ytree
>>> a = ytree.load('tree_0_0_0.dat')
>>> my_tree = a[0]
>>> print(my_tree['tree', 'mass'].to('Msun'))
[6.57410072e+14 6.57410072e+14 6.53956835e+14 6.50071942e+14 ...
 2.60575540e+12 2.17122302e+12 2.17122302e+12] Msun
```

A list of all currently supported formats can be found in the online
[documentation](https://ytree.readthedocs.io/en/latest/Arbor.html#loading-merger-tree-data). If
you would like to see support added for another format, we would be
happy to work with you to make it happen. In principle, any type of
tree-like data where an object has one or more ancestors and a single
descendent can be supported.

## Installation

`ytree` can be installed with pip:

```
pip install ytree
```

To get the development version, clone this repository and install like this:

```
git clone https://github.com/ytree-project/ytree
cd ytree
pip install -e .
```

## Getting Started

The [ytree documentation](https://ytree.readthedocs.io) will walk you
through installation, get you started analyzing merger trees, and help
you become a contributor to the project. Have a look!

## Sample Data

Sample data for all merger tree formats supported by `ytree` is available on the
[yt Hub](https://girder.hub.yt/) in the
[ytree data](https://girder.hub.yt/#collection/59835a1ee2a67400016a2cda) collection.

## Contributing

`ytree` would be much better with your contribution!  As an extension of
[the yt Project](https://yt-project.org/), we follow the yt
[guidelines for contributing](https://github.com/yt-project/yt#contributing).

## Citing `ytree`

If you use `ytree` in your work, please cite the following:

```
Smith et al., (2019). ytree: A Python package for analyzing merger trees.
Journal of Open Source Software, 4(44), 1881,
https://doi.org/10.21105/joss.01881
```

For BibTeX users:

```
  @article{ytree,
    doi = {10.21105/joss.01881},
    url = {https://doi.org/10.21105/joss.01881},
    year  = {2019},
    month = {dec},
    publisher = {The Open Journal},
    volume = {4},
    number = {44},
    pages = {1881},
    author = {Britton D. Smith and Meagan Lang},
    title = {ytree: A Python package for analyzing merger trees},
    journal = {Journal of Open Source Software}
  }
```

If you would like to also cite the specific version of `ytree` used in
your work, include the following reference:

```
@software{britton_smith_2022_5959655,
  author       = {Britton Smith and
                  Meagan Lang and
                  Juanjo Bazán},
  title        = {ytree-project/ytree: ytree 3.1.1 Release},
  month        = feb,
  year         = 2022,
  publisher    = {Zenodo},
  version      = {ytree-3.1.1},
  doi          = {10.5281/zenodo.5959655},
  url          = {https://doi.org/10.5281/zenodo.5959655}
}
```

## Resources

 * The latest documentation can be found at
   https://ytree.readthedocs.io.

 * The [ytree
   paper](https://joss.theoj.org/papers/10.21105/joss.01881) in the
   [Journal of Open Source Software](https://joss.theoj.org/).

 * `ytree` is an extension of [the yt
   Project](https://yt-project.org/). The [yt-project community
   resources](https://github.com/yt-project/yt#resources) can be used
   for ytree-related communication. The `ytree` developers can usually
   be found on the yt project Slack channel.
