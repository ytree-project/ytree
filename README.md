# ytree

[![Build Status](https://travis-ci.org/ytree-project/treefarm.svg?branch=master)](https://travis-ci.org/ytree-project/treefarm)
[![Coverage Status](https://coveralls.io/repos/github/ytree-project/ytree/badge.svg?branch=master)](https://coveralls.io/github/ytree-project/ytree?branch=master)
[![Documentation Status](https://readthedocs.org/projects/ytree/badge/?version=latest)](http://ytree.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/ytree.svg)](https://badge.fury.io/py/ytree)
[![DOI](https://zenodo.org/badge/98564214.svg)](https://zenodo.org/badge/latestdoi/98564214)

This is ytree, a [yt](https://github.com/yt-project/yt) extension for
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

ytree can be installed with pip:

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

Below is a notebook that demonstrates how to use ytree with merger tree data.  For
more information, see the full [ytree documentation](https://ytree.readthedocs.io).

 * [Introduction](https://github.com/ytree-project/ytree/blob/master/doc/source/notebooks/Intro_to_ytree.ipynb)

## Sample Data

Sampled data for all merger tree formats supported by ytree is available on the
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

 * ytree is an extension of [the yt
   Project](https://yt-project.org/). The [yt-project community
   resources](https://github.com/yt-project/yt#resources) can be used
   for ytree-related communication. The ytree developers can usually
   be found on the yt project Slack channel.
