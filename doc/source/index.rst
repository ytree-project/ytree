.. ytree documentation master file, created by
   sphinx-quickstart on Wed Aug 31 10:54:10 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to ytree.
=================

ytree is a tool for working with merger-tree data from multiple sources.
ytree is an extension of the `yt <http://yt-project.org/>`_ analysis toolkit
and provides a similar interface for merger-tree data that includes universal
field names, derived fields, and symbolic units.  ytree can create
merger-trees from Gadget FoF/Subfind catalogs, either for all halos or for a
specific set of halos.  ytree is able to load in merger-tree from the following
formats:

- `consistent-trees <https://bitbucket.org/pbehroozi/consistent-trees>`_
- `Rockstar <https://bitbucket.org/gfcstanford/rockstar>`_ halo catalogs
  without consistent-trees
- merger-trees made with ytree

All formats can be saved with a universal format that can be reloaded
with ytree.  Individual trees for single halos can also be saved.

Table of Contents
=================

.. toctree::
   :maxdepth: 2

   Installation.rst
   Arbor.rst
   TreeFarm.rst
   Conduct.rst
   Contributing.rst
   reference.rst

Help
====

Since ytree is heavily based on `yt <http://yt-project.org/>`_, the best
way to get help is by joining the `yt users list
<http://lists.spacepope.org/listinfo.cgi/yt-users-spacepope.org>`_.  Feel
free to post any questions or ideas for development.

Citing ytree
============

If you use ytree in your work, please cite it as "ytree, written by
Britton smith" with a footnote pointing to http://ytree.readthedocs.io.

Search
======

* :ref:`search`

