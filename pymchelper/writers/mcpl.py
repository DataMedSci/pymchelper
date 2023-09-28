import logging
from pathlib import Path
import struct

import numpy as np
import pymchelper

from pymchelper.page import Page
from pymchelper.shieldhit.detector.detector_type import SHDetType
from pymchelper.writers.writer import Writer

logger = logging.getLogger(__name__)


class MCPLWriter(Writer):
    """MCPL data writer"""

    def __init__(self, output_path: str, _):
        super().__init__(output_path)
        self.output_path = self.output_path.with_suffix(".mcpl")

    def write_single_page(self, page: Page, output_path: Path):
        """TODO"""
        logger.info("Writing page to: %s", str(output_path))

        # special case for MCPL data
        if page.dettyp == SHDetType.mcpl:

            # first part of the header
            header_bytes = "MCPL".encode('ascii')  # magic number
            header_bytes += "003".encode('ascii')  # version
            header_bytes += "L".encode('ascii')  # little endian
            header_bytes += struct.pack("<Q", page.data.shape[1])  # number of particles
            header_bytes += struct.pack("<I", 0)  # number of custom comments
            header_bytes += struct.pack("<I", 0)  # number of custom binary blobs
            header_bytes += struct.pack("<I", 0)  # user flags disabled
            header_bytes += struct.pack("<I", 0)  # polarisation disabled
            header_bytes += struct.pack("<I", 1)  # single precision for floats
            header_bytes += struct.pack("<i", 0)  # all particles have PDG code
            header_bytes += struct.pack("<I", 32)  # data length
            header_bytes += struct.pack("<I", 1)  # universal weight

            # second part of the header
            header_bytes += struct.pack("<d", 1)  # universal weight value

            # data arrays
            source_name = f"pymchelper {pymchelper.__version__}"
            header_bytes += struct.pack("<I", len(source_name))  # length of the source name
            header_bytes += source_name.encode('ascii')  # source name

            # particle data
            # need to fix the structure according to MCPL format
            # see https://mctools.github.io/mcpl/mcpl.pdf#nameddest=section.3
            # we use numpy to speed up the process for large arrays

            # Create a structured array with named fields, as some of the fields have different types
            dt = np.dtype([('x', np.float32), ('y', np.float32), ('z', np.float32), ('fp1', np.float32),
                           ('fp2', np.float32), ('uz', np.float32), ('time', np.float32), ('pdg', np.uint32)])
            data_bytes = np.empty(page.data.shape[1], dtype=dt)

            # Assign values to the fields
            data_bytes['x'] = page.data[1]
            data_bytes['y'] = page.data[2]
            data_bytes['z'] = page.data[3]
            data_bytes['fp1'] = page.data[4]  # ux by default
            data_bytes['fp2'] = page.data[5]  # uy by default
            data_bytes['time'] = 0
            data_bytes['pdg'] = page.data[0]

            ux2 = page.data[4]**2
            uy2 = page.data[5]**2
            uz2 = page.data[6]**2
            sign = np.ones_like(page.data[6], dtype=int)

            # find the maximum component of the direction vector
            # condition below defines the case where the maximum component is ux
            condition_1 = np.logical_and(ux2 >= uy2, ux2 > uz2)
            # condition below defines the case where the maximum component is uy
            condition_2 = np.logical_and(uy2 > ux2, uy2 > uz2)
            # by exclusion, the remaining case is where the maximum component is uz
            condition_3 = np.logical_not(np.logical_or(condition_1, condition_2))

            # fill the arrays according to the maximum component
            # lets start with the case where the maximum component is uz
            sign[(page.data[6] < 0) & condition_3] = -1

            # fill the arrays according to the maximum component ux
            sign[(page.data[4] < 0) & condition_1] = -1  # negative sign of ux
            data_bytes['fp1'][condition_1] = 1 / page.data[6][condition_1]  # 1/uz
            data_bytes['fp2'][condition_1] = page.data[5][condition_1]  # uy

            # fill the arrays according to the maximum component uy
            sign[(page.data[5] < 0) & condition_2] = -1  # sign of uy
            data_bytes['fp1'][condition_2] = page.data[4][condition_2]  # ux
            data_bytes['fp2'][condition_2] = 1 / page.data[6][condition_2]  # 1/uz

            data_bytes['uz'] = sign * page.data[7]

            data_bytes = data_bytes.tobytes()

            output_path.write_bytes(header_bytes + data_bytes)
            return
