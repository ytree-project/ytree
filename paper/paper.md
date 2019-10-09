---
title: 'ytree: A Python package for merger trees'
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

# Summary

The formation of cosmological structure is dominated, especially on large scales,
by the force of gravity. In the early Universe, matter is very evenly distributed,
with only small fluxuations about the average density. Overdense regions undergo
gravitational collapse to form bound structures, called halos, which will host
galaxies within them. Halos grow via accretion of the surrounding material and
mergers with other halos. This process of merging to form increasingly massive
halos is very naturally conceptualized as an inverted tree, where small branches
connect up to continually larger ones, leading eventually to the trunk.

One of the main products of a cosmological simulation is a series of catalogs
of all halos within the simulated volume at a number of epochs. Halos within
succesive catalogs can be linked together to create merger trees that describe a
halo's growth history. A variety of algorithms and software packages exist for
both halo identification and merger tree calculation, resulting in a plethora
of different data formats that are non-trivial to load back into memory. A range
of negative consequences arise from this situation, including difficulty of
comparing methods or scientific results and users being locked into less than
ideal workflows.

The ``ytree`` package [@ytree] is an extension of the ``yt`` analysis toolkit
[@yt] for ingesting and working with merger tree data from multiple sources.
The ``ytree`` package provides a means to load diverse merger tree data sets
into common Python data structures, analogous to what ``yt`` does for spatial
data. A merger tree data set loaded by ``ytree`` is returned to the user as a
NumPy [@numpy] array of objects representing the final halo, or node, in each
merger tree. Each node object contains pointers to node objects representing its
immediate ancestors. This allows the user to intuitively navigate the tree
structure for analysis tasks. Data fields, such as position, velocity, and mass,
can be queried for any node object, for the entire tree stemming from a given node,
or for just the line of most significant progenitors (typically the most massive).
All data structure creation and field data loading is done on-demand to limit
unnecessary computation.

The ``ytree`` package has been used for semi-analytic galaxy formation models
[@2018ApJ...859...67C]; following halo trajectories in zoom-in simulations
[@2019ApJ...882..156H]; and for studying simulated galaxy properties
[@2018MNRAS.480.3762S, @2019MNRAS.489.4574G].

# Acknowledgements

This work was supported by NSF AST-1615848 (BDS).

# References
