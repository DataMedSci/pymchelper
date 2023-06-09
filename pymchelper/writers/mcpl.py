import logging
from pathlib import Path
import struct
import pymchelper

from pymchelper.estimator import Estimator
from pymchelper.page import Page
from pymchelper.shieldhit.detector.detector_type import SHDetType
from pymchelper.writers.writer import Writer

logger = logging.getLogger(__name__)


class MCPLWriter(Writer):
    def __init__(self, output_path: str, _):
        self.output_path = Path(output_path).with_suffix(".mcpl")

    def write_single_page(self, page: Page, output_path: Path):
        """TODO"""
        logger.info("Writing page to: %s", str(output_path))

        # special case for MCPL data
        if page.dettyp == SHDetType.mcpl:
            
            # first part of the header
            bytes_to_write = "MCPL".encode('ascii') # magic number
            bytes_to_write += "003".encode('ascii') # version
            bytes_to_write += "L".encode('ascii') # little endian
            bytes_to_write += struct.pack("<Q", page.data.shape[1]) # number of particles
            bytes_to_write += struct.pack("<I", 0) # number of custom comments
            bytes_to_write += struct.pack("<I", 0) # number of custom binary blobs
            bytes_to_write += struct.pack("<I", 0) # user flags disabled
            bytes_to_write += struct.pack("<I", 0) # polarisation disabled
            bytes_to_write += struct.pack("<I", 1) # single precision for floats
            bytes_to_write += struct.pack("<i", 0) # all particles have PDG code
            bytes_to_write += struct.pack("<I", 4) # data length
            bytes_to_write += struct.pack("<I", 1) # universal weight

            # second part of the header
            bytes_to_write += struct.pack("<d", 1) # universal weight value

            # data arrays
            source_name = f"pymchelper {pymchelper.__version__}"
            bytes_to_write += struct.pack("<I", len(source_name)) # length of the source name
            bytes_to_write += source_name.encode('ascii') # source name

            # particle data
            # iterate over rows in the data array page.data
            # need to fix the structure according to MCPL format
            # see https://mctools.github.io/mcpl/mcpl.pdf#nameddest=section.3
            for row in page.data.T:
                pdg, x, y, z, ux, uy, uz, E = row
                bytes_to_write += struct.pack("<d", x) # x
                bytes_to_write += struct.pack("<d", y) # y
                bytes_to_write += struct.pack("<d", z) # z
                bytes_to_write += struct.pack("<d", ux) # ux
                bytes_to_write += struct.pack("<d", uy) # uy
                bytes_to_write += struct.pack("<d", E) # uz
                bytes_to_write += struct.pack("<d", 0) # time
                bytes_to_write += struct.pack("<I", int(pdg)) # E
                print(f"pdg: {pdg}, x: {x}, y: {y}, z: {z}, ux: {ux}, uy: {uy}, uz: {uz}, E: {E}")

            output_path.write_bytes(bytes_to_write)
            return
