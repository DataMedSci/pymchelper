.. highlight:: bash

.. role:: bash(code)
   :language: bash

HDF file
========

Saves data in HDF binary file format.
HDF is designed to store large amounts of data organized in convenient way.
One HDF file can handle many single- or multi-dimensional tables.
For every detector a single file with :bash:`.h5` extension is written.

An example usage
----------------

Conversion is done using standard command::

    convertmc HDF --many "*.bdo"

Assuming that we had "dose" detector output saved to :bash:`dose0001.bdo`, :bash:`dose0002.bdo` and :bash:`dose0003.bdo`,
we should expect to get :bash:`dose.h5` as an output file.


Data reconstruction
-------------------

Data can be extracted from HDF file with following Python code:

.. code-block:: python

   import h5py

   # reading data and attributes from HDF file
    with h5py.File('dose.h5', 'r') as hf:
        data = hf['data'][:]  # numpy array with data storage
        attr = dict(hf['data'].attrs.items())  # dictionary with metadata

