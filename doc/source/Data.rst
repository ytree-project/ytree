.. _sample-data:

Sample Data
===========

Sample datasets for every supported data format are available for download
from the `yt Hub <https://girder.hub.yt/>`__ in the
`ytree data <https://girder.hub.yt/#collection/59835a1ee2a67400016a2cda>`__
collection.  The entire collection (about 979 MB) can be downloaded
via the yt Hub's web interface by clicking on "Actions" drop-down menu on
the far right and selecting "Download collection." Individual datasets can
also be downloaded from this interface. Finally, the entire collection can
be downloaded through the girder-client interface:

.. code-block:: bash

   $ pip install girder-client
   $ girder-cli --api-url https://girder.hub.yt/api/v1 download 59835a1ee2a67400016a2cda ytree_data
