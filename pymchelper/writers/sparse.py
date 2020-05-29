import logging

import numpy as np

logger = logging.getLogger(__name__)


class SparseWriter:
    """
    Supports writing sparse matrix format
    """
    def __init__(self, filename, options):
        self.filename = filename
        if not self.filename.endswith(".npz"):
            self.filename += ".npz"

        self.threshold = options.threshold
        logger.info("Sparse threshold {:g}".format(self.threshold))

    def write(self, estimator):
        if len(estimator.pages) > 1:
            print("Conversion of data with multiple pages not supported yet")
            return False

        page = estimator.pages[0]

        # estimator.data array is a 3-D numpy array
        # some of its dimensions may be as well ones and the array reduced to 0,1 or 2-D
        all_items = page.data.size
        logger.info("Number of all items: {:d}".format(all_items))

        # prepare a cut to select values which norm is greater than threshold
        # default value of threshold is zero, in this case non-zero values will be selected
        # cut will be 3-D arrays of booleans
        # note that numpy allocates here same amount of memory as for original data
        thres_cut = np.abs(page.data) > self.threshold
        passed_items = np.sum(thres_cut)
        logger.info("Number of items passing threshold: {:d}".format(passed_items))
        logger.info("Sparse matrix compression rate: {:g}".format(passed_items / all_items))

        # select indices which pass threshold
        # we get here a plain python tuple of 3-elements
        # first element is numpy array of indices along X-axis, second for Y axis and third for Z
        # note that such table cannot be used directly to index numpy arrays
        indices = np.argwhere(thres_cut)

        # select data which pass threshold and save it as plain 1-D numpy array
        filtered_data = page.data[thres_cut]

        # save file to NPZ file format
        np.savez(file=self.filename,
                 data=filtered_data,
                 indices=indices,
                 shape=page.data.shape)

        return 0
