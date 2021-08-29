Welcome to ytree.
=================

``ytree`` is a tool for working with merger tree data from multiple
sources. ``ytree`` is an extension of the `yt
<https://yt-project.org/>`_ analysis toolkit and provides a similar
interface for merger tree data that includes universal field names,
derived fields, symbolic units, parallel functionality, and a
framework for performing complex analysis. ``ytree`` is able to load
in merger tree from the following formats:

- :ref:`load-ahf`
- :ref:`load-ctrees`
- :ref:`load-ctrees-hdf5`
- :ref:`load-lhalotree`
- :ref:`load-lhalotree-hdf5`
- :ref:`load-moria`
- :ref:`load-rockstar`
- :ref:`load-treefarm`
- :ref:`load-treefrog`

See :ref:`loading` for instructions specific to each format.
All formats can be :ref:`resaved with a universal format <saving-trees>` that
can be :ref:`reloaded with ytree <load-ytree>`. Individual trees for single
halos can also be saved.

I want to make merger trees!
============================

If you have halo catalog data that can be loaded by
`yt <https://yt-project.org/>`_, then you can use the
`treefarm <https://treefarm.readthedocs.io/>`_ package to create
merger trees. `treefarm <https://treefarm.readthedocs.io/>`_ was
once a part of ``ytree``, but is now its own thing.

Table of Contents
=================

.. toctree::
   :maxdepth: 2

   Installation.rst
   Data.rst
   Frames.rst
   Arbor.rst
   Fields.rst
   Plotting.rst
   Parallelism.rst
   Analysis.rst
   Examples.rst
   Conduct.rst
   Contributing.rst
   Developing.rst
   Help.rst
   Citing.rst
   reference.rst

.. include:: ../../CITATION.rst

Search
======

* :ref:`search`
