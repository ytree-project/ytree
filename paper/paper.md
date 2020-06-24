---
title: 'ytree: A Python package for analyzing merger trees'
tags:
  - Python
  - astronomy
  - astrophysics
  - merger tree
  - structure formation
  - galaxies
authors:
  - name: Britton D. Smith
    orcid: 0000-0002-6804-630X
    affiliation: 1
  - name: Meagan Lang
    orcid: 0000-0002-2058-2816
    affiliation: 2
affiliations:
 - name: University of Edinburgh
   index: 1
 - name: University of Illinois at Urbana-Champaign
   index: 2
date: 4 October 2019
bibliography: paper.bib
---

# Summary

The formation of cosmological structure is dominated, especially on
large scales, by the force of gravity. In the early Universe, matter
is distributed homogeneously, with only small fluctuations about the
average density. Overdense regions undergo gravitational collapse to
form bound structures, called halos, which will host galaxies within
them. Halos grow via accretion of the surrounding material and by
merging with other halos. This process of merging to form increasingly
massive halos is naturally conceptualized as an inverted tree, where
small branches connect up to continually larger ones, leading
eventually to a trunk.

One of the main products of cosmological simulations is a series of
catalogs of halos within the simulated volume at different
epochs. Halos within successive epochs can be linked together to
create merger trees that describe a halo’s growth history. An example
of such a merger tree is shown in Figure 1. A variety of algorithms
and software packages exist for both halo identification and merger
tree calculation, resulting in a plethora of different data formats
that are non-trivial to load back into memory. A range of negative
consequences arise from this situation, including the difficulty of
comparing methods or scientific results and users being locked into
less than ideal workflows.

![A visualization of a merger tree. Each circle represents a halo with
 lines connecting it to its descendent upward and its ancestors
 downward, with the size of the circle proportional to the halo's
 mass. Red circles denote the line of the most massive ancestors
 of the primary halo at a given epoch. The merger tree was created
 with the ``consistent-trees`` [@ctrees] merger tree code, loaded by
 ``ytree``, and visualized with ``pydot`` [@pydot] and ``graphviz``
 [@graphviz].](tree.png)

The ``ytree`` package [@ytree] is an extension of the ``yt`` analysis
toolkit [@yt] for ingesting and analyzing merger tree data from
multiple sources. The ``ytree`` package provides a means to load
diverse merger tree data sets into common Python data structures,
analogous to what ``yt`` does for spatial data. A merger tree data set
loaded by ``ytree`` is returned to the user as a NumPy [@numpy] array
of objects representing the final halo, or node, in each merger
tree. Each node object contains pointers to node objects representing
its immediate ancestors and descendent. This allows the user to
intuitively navigate the tree structure.

Data fields, such as position, velocity, and mass, can be queried for
any node object, for the entire tree stemming from a given node, or
for just the line of most significant progenitors (typically the most
massive). Field data are returned as ``unyt_quantity`` or
``unyt_array`` objects [@unyt], subclasses of the NumPy array with
support for symbolic units. All data structure creation and field data
loading is done on-demand to limit unnecessary computation. Analogous
to ``yt``, derived fields can be created as linear combinations of any
existing fields by supplying a function that accepts a dictionary-like
object that can be expected to contain arrays of the dependent field
data. Any portion of a merger tree data set can be saved to a
``ytree`` format (based on HDF5 and using ``h5py`` [@h5py]) that has
somewhat faster field loading than most of the supported data
formats. This also allows a subset of data to be extracted for greater
portability and for saving newly created fields resulting from
expensive analysis.

The ``ytree`` package has been used for semi-analytic galaxy formation
models [@cote2018]; following halo trajectories in zoom-in simulations
[@hummels2019]; and for studying simulated galaxy properties
[@smith2018; @garrisonkimmel2019].

# Acknowledgements

Britton acknowledges the amazing ``yt`` community for being amazing as
well as financial support from NSF grant AST-1615848. M. Lang would
like to acknowledge the Gordon and Betty Moore Foundation’s
Data-Driven Discovery Initiative for supporting her contributions to
this work through Grant GBMF4561 to Matthew Turk.

# References
