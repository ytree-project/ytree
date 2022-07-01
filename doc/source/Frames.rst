.. _frames:

An Important Note on Comoving and Proper Units
==============================================

Users of ``yt`` are likely familiar with conversion from proper to comoving
reference frames by adding "cm" to a unit. For example, proper "Mpc"
becomes comoving with "Mpccm". This conversion relies on all the data
being associated with a single redshift. This is not possible here
because the dataset has values for multiple redshifts. To account for
this, the proper and comoving unit systems are set to be equal to each
other.

.. code-block:: python

   >>> print (a.box_size)
   100.0 Mpc/h
   >>> print (a.box_size.to("Mpccm/h"))
   100.0 Mpccm/h

Data should be assumed to be in the reference frame in which it
was saved. For length scales, this is typically the comoving frame.
When in doubt, the safest unit to use for lengths is "unitary", which
a system normalized to the box size.

.. code-block:: python

   >>> print (a.box_size.to("unitary"))
   1.0 unitary
