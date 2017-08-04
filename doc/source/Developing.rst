.. _developing:

Developer Guide
===============

ytree is developed using the same conventions as yt.  The `yt
Developer Guide <http://yt-project.org/docs/dev/developing/index.html>`_
is a good reference for code style, communication with other developers,
working with git, and issuing pull requests.  Below is a brief guide of
aspects that are specific to ytree.

Contributing in a Nutshell
--------------------------

Step zero, get out of that nutshell!

After that, the process for making contributions to ytree is roughly as
follows:

1. Fork the `main ytree repository <https://github.com/brittonsmith/ytree>`__.

2. Create a new branch.

3. Make changes.

4. Run tests.  Return to step 3, if needed.

5. Issue pull request.

The yt Developer Guide and `github <https://github.com/>`__ documentation
will help with the mechanics of git and pull requests.

Testing
-------

The ytree source comes with a series of tests that can be run to
ensure nothing unexpected happens after changes have been made.  These
tests will automatically run when a pull request is issued or updated,
but they can also be run locally very easily.  At present, the suite
of tests for ytree takes about three minutes to run.

Testing Data
^^^^^^^^^^^^

The first order of business is to obtain the sample datasets.  See
:ref:`sample-data` for how to do so.  Next, ytree must be configure to
know the location of this data.  This is done by creating a configuration
file in your home directory at the location ``~/.config/ytree/ytreerc``.

.. code-block:: bash

   $ mkdir -p ~/.config/ytree
   $ echo [ytree] > ~/.config/ytree/ytreerc
   $ echo test_data_dir = /Users/britton/ytree_data >> ~/.config/ytree/ytreerc
   $ cat ~/.config/ytree/ytreerc
   [ytree]
   test_data_dir = /Users/britton/ytree_data

This path should point to the outer directory containing all the
sample datasets.

Run the Tests
^^^^^^^^^^^^^

Before running the tests, you will the ``pytest`` and ``flake8`` packages.
These can be installed with pip.

.. code-block:: bash

   $ pip install pytest flake8

Once installed, the tests are run from the top level of the ytree
source.

.. code-block:: bash

   $ pytest tests
   ============================= test session starts ==============================
   platform darwin -- Python 3.6.0, pytest-3.0.7, py-1.4.32, pluggy-0.4.0
   rootdir: /Users/britton/Documents/work/yt/extensions/ytree/ytree, inifile:
   collected 16 items

   tests/test_arbors.py ........
   tests/test_flake8.py .
   tests/test_saving.py ...
   tests/test_treefarm.py ..
   tests/test_ytree_1x.py ..

   ========================= 16 passed in 185.03 seconds ==========================
