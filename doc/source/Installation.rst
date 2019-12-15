.. _installation:

Installation
============

``ytree``'s main dependency is `yt <http://yt-project.org/>`_.  Once you
have installed ``yt`` following the instructions `here
<http://yt-project.org/#getyt>`__, ``ytree`` can be installed using pip.

.. code-block:: bash

    $ pip install ytree

If you'd like to install the development version, the repository can
be found at `<https://github.com/ytree-project/ytree>`__.  This can be
installed by doing:

.. code-block:: bash

   $ git clone https://github.com/ytree-project/ytree
   $ cd ytree
   $ pip install -e .

What version do I have?
=======================

To see what version of ``ytree`` you are using, do the following:

.. code-block:: python

   >>> import ytree
   >>> print (ytree.__version__)
