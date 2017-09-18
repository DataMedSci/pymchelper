.. highlight:: bash

.. role:: bash(code)
   :language: bash

Sparse matrix data
==================

Sparse matrix format can greatly reduce size on disk in case when most of the matrix is occupied with zeros.
This detector writes for every input detector a file with :bash:`.npz` extension which contains:

* shape of detector data: tuple of 3 numbers holding nx, ny and nz
* tuple of 3 numpy arrays with X,Y and Z coordinates, pointing to non-zero data cells
* plain, 1D numpy array with non-zero data values

Such format is similar to so called COO-rdinate format for 2D sparse matrices. Here it is used
for any kind of data, with dimensionality between 0 and 3.

Output file is saved in uncompressed NPZ numpy data format,
for details see https://docs.scipy.org/doc/numpy/reference/generated/numpy.savez.html


An example usage
----------------

Conversion is done using standard command::

    convertmc sparse --many "*.bdo"


Assuming that we had "dose" detector output saved to :bash:`dose0001.bdo`, :bash:`dose0002.bdo` and :bash:`dose0003.bdo`,
we should expect to get :bash:`dose.npz` as an output file.

Data reconstruction
-------------------

Sparse data can be extracted from NPZ file with following Python code:

.. code-block:: python

   # load contents of NPZ file:
   npzfile = np.load(filename)
   data = npzfile['data']   # plain 1-D numpy array
   indices = npzfile['indices']  # 3-elements tuple with array of coordinates
   shape = npzfile['shape'] # 3-element shape tuple

   # reconstruct normal form of matrix from sparse data
   result = np.zeros(shape)
   for ind, dat in zip(indices, data):
       result[tuple(ind)] = dat


Threshold value
---------------

Additionally threshold can be specified to remove noisy data. In this case, all data cells
with absolute value less or equal than threshold will be treated as zeros.
Please note that after reconstructing from sparse format we will not get the original data,
as values lower than threshold will be overwritten with zeros.
An example usage::

    convertmc sparse --many "*.bdo" --threshold 1e-7
