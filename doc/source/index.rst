.. ytree documentation master file, created by
   sphinx-quickstart on Wed Aug 31 10:54:10 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to ytree's documentation!
=================================

ytree is a merger-tree code based on the `yt <http://yt-project.org/>`_
analysis toolkit.  ytree can create merger-trees from Gadget FoF/Subfind
catalogs, either for all halos or for a specific set of halos.  ytree is
able to load in merger-tree from the following formats:

- `consistent-trees <https://bitbucket.org/pbehroozi/consistent-trees>`_
- `Rockstar <https://bitbucket.org/gfcstanford/rockstar>`_ halo catalogs
  without consistent-trees
- merger-trees made with ytree

All formats can be saved with a universal format that can be reloaded
with ytree.  Individual trees for single halos can also be saved.  Similar
to yt, fields queried for halos or trees are returned with units.

Installation
============

ytree's main dependency is `yt <http://yt-project.org/>`_.  Once you
have installed yt following the instructions `here
<http://yt-project.org/#getyt>`_, ytree can be installed using pip.

.. code-block:: bash

    pip install ytree

And that's it!

Using ytree
===========

.. toctree::
   :maxdepth: 2

   Arbor.rst
   TreeFarm.rst

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

