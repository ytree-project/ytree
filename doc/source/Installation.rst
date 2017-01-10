.. _installation:

Installation
============

ytree's main dependency is `yt <http://yt-project.org/>`_.  Once you
have installed yt following the instructions `here
<http://yt-project.org/#getyt>`__, ytree can be installed using pip.

.. code-block:: bash

    pip install ytree

If you'd like to install the development version or don't want to use
pip, the mercurial repository for ytree can be found
`here <https://bitbucket.org/brittonsmith/ytree>`__.  To clone the
repositry, just do:

.. code-block:: bash

   hg clone https://bitbucket.org/brittonsmith/ytree

Then, install with one of the following two methods:

.. code-block:: bash

   cd ytree
   python setup.py develop

or

.. code-block:: bash

   cd ytree
   pip install -e .
