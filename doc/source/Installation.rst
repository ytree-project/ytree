.. _installation:

Installation
============

Installing Stable Releases
--------------------------

Stable releases of ``ytree`` can be installed with either ``pip`` or
``conda``.

pip
^^^

.. code-block:: bash

    $ pip install ytree

conda
^^^^^

.. code-block: bash

   $ conda install -c conda-forge ytree

Installing from Source
----------------------

If you'd like to install the development version, the repository can
be found at `<https://github.com/ytree-project/ytree>`__. This can be
installed by doing:

.. code-block:: bash

   $ git clone https://github.com/ytree-project/ytree
   $ cd ytree
   $ pip install -e .

Installing yt
-------------

``ytree``'s main dependency is `yt
<http://yt-project.org/>`_. Periodically, the development version of
``ytree`` may require installing the development version of
``yt``. See the `yt installation instructions
<http://yt-project.org/#getyt>`__ for how to do that.

What version do I have?
=======================

To see what version of ``ytree`` you are using, do the following:

.. code-block:: python

   >>> import ytree
   >>> print (ytree.__version__)
