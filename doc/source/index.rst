Welcome to ytree.
=================

``ytree`` is a tool for working with merger-tree data from multiple sources.
``ytree`` is an extension of the `yt <https://yt-project.org/>`_ analysis toolkit
and provides a similar interface for merger-tree data that includes universal
field names, derived fields, and symbolic units. ``ytree`` is able to load in
merger-tree from the following formats:

- `Amiga Halo Finder <http://popia.ft.uam.es/AHF/Download.html>`_
- `Consistent-Trees <https://bitbucket.org/pbehroozi/consistent-trees>`_
- `LHaloTree <https://ui.adsabs.harvard.edu/abs/2005MNRAS.364.1105S>`_
- `Rockstar <https://bitbucket.org/gfcstanford/rockstar>`_ halo catalogs
  without consistent-trees
- `treefarm <https://treefarm.readthedocs.io/>`_

All formats can be :ref:`resaved with a universal format <saving-trees>` that
can be reloaded with ``ytree``.  Individual trees for single halos can also be
saved.

I want to make merger-trees!
============================

If you have halo catalog data that can be loaded by
`yt <https://yt-project.org/>`_, then you can use the
`treefarm <https://treefarm.readthedocs.io/>`_ package to create
merger-trees. `treefarm <https://treefarm.readthedocs.io/>`_ was
once a part of ``ytree``, but is now its own thing.

Table of Contents
=================

.. toctree::
   :maxdepth: 2

   Installation.rst
   Data.rst
   Arbor.rst
   Fields.rst
   Plotting.rst
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

