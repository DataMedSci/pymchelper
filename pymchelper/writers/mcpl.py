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
            bytes_to_write = "MCPL".encode('ascii')  # magic number
            bytes_to_write += "003".encode('ascii')  # version
            bytes_to_write += "L".encode('ascii')  # little endian
            bytes_to_write += struct.pack("<Q", page.data.shape[1])  # number of particles
            bytes_to_write += struct.pack("<I", 0)  # number of custom comments
            bytes_to_write += struct.pack("<I", 0)  # number of custom binary blobs
            bytes_to_write += struct.pack("<I", 0)  # user flags disabled
            bytes_to_write += struct.pack("<I", 0)  # polarisation disabled
            bytes_to_write += struct.pack("<I", 1)  # single precision for floats
            bytes_to_write += struct.pack("<i", 0)  # all particles have PDG code
            bytes_to_write += struct.pack("<I", 4)  # data length
            bytes_to_write += struct.pack("<I", 1)  # universal weight

            # second part of the header
            bytes_to_write += struct.pack("<d", 1)  # universal weight value

            # data arrays
            source_name = f"pymchelper {pymchelper.__version__}"
            bytes_to_write += struct.pack("<I", len(source_name))  # length of the source name
            bytes_to_write += source_name.encode('ascii')  # source name

            # particle data
            # iterate over rows in the data array page.data
            # need to fix the structure according to MCPL format
            # see https://mctools.github.io/mcpl/mcpl.pdf#nameddest=section.3

            print(page.data.shape)
            pdg = page.data[0]
            x = page.data[1]
            y = page.data[2]
            z = page.data[3]
            ux = page.data[4]
            uy = page.data[5]
            uz = page.data[6]
            E = page.data[7]
            fp1 = np.empty_like(ux)
            fp2 = np.empty_like(uy)
            sign = np.ones_like(x, dtype=int)

            condition_1 = np.logical_and(np.logical_and(ux * ux > uy * uy, ux * ux > uz * uz), ux < 0)
            condition_2 = np.logical_and(np.logical_and(uy * uy > ux * ux, uy * uy > uz * uz), uy < 0)
            condition_3 = np.logical_and(np.logical_and(uz * uz >= ux * ux, uz * uz >= uy * uy), uz < 0)

            sign[ux < 0] = -1
            fp1[condition_1] = 1 / uz[condition_1]
            fp2[condition_1] = uy[condition_1]

            sign[uy < 0] = -1
            fp1[condition_2] = ux[condition_2]
            fp2[condition_2] = 1 / uz[condition_2]

            sign[uz < 0] = -1
            fp1[condition_3] = ux[condition_3]
            fp2[condition_3] = uy[condition_3]

            bytes_to_write = np.empty(page.data.shape, dtype=np.float32)
            bytes_to_write[0] = x
            bytes_to_write[1] = y
            bytes_to_write[2] = z
            bytes_to_write[3] = fp1
            bytes_to_write[4] = fp2
            bytes_to_write[5] = sign * E
            bytes_to_write[6] = 0
            bytes_to_write[7] = pdg.astype(np.uint32)

            bytes_to_write = bytes_to_write.tobytes()

            # for i, row in enumerate(page.data.T):

            #     pdg, x, y, z, ux, uy, uz, E = row

            #     # adaptive projection packing
            #     fp1: float = float('nan')
            #     fp2: float = float('nan')
            #     sign: int = 1
            #     if ux * ux > uy * uy and ux * ux > uz * uz:
            #         if ux < 0:
            #             sign = -1
            #         fp1 = 1 / uz
            #         fp2 = uy
            #     if uy * uy > ux * ux and uy * uy > uz * uz:
            #         if uy < 0:
            #             sign = -1
            #         fp1 = ux
            #         fp2 = 1 / uz
            #     if uz * uz >= ux * ux and uz * uz >= uy * uy:
            #         if uz < 0:
            #             sign = -1
            #         fp1 = ux
            #         fp2 = uy

            #     bytes_to_write += struct.pack("<f", x)  # x
            #     bytes_to_write += struct.pack("<f", y)  # y
            #     bytes_to_write += struct.pack("<f", z)  # z
            #     bytes_to_write += struct.pack("<f", fp1)  # FP1 (mostly ux)
            #     bytes_to_write += struct.pack("<f", fp2)  # FP2 (mostly uy)
            #     bytes_to_write += struct.pack("<f", sign * E)  # uz
            #     bytes_to_write += struct.pack("<f", 0)  # time
            #     bytes_to_write += struct.pack("<I", int(pdg))  # pdg

            output_path.write_bytes(bytes_to_write)
            return
