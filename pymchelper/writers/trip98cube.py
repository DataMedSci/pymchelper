import getpass
import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pymchelper

from pymchelper.estimator import Estimator
from pymchelper.page import Page
from pymchelper.shieldhit.detector.detector_type import SHDetType
from pymchelper.shieldhit.detector.estimator_type import SHGeoType
from pymchelper.writers.writer import Writer

logger = logging.getLogger(__name__)

LET_TYPES = (SHDetType.dlet, SHDetType.tlet, SHDetType.dletg, SHDetType.tletg)
CARTESIAN_GEOMETRIES = (SHGeoType.msh, SHGeoType.dmsh, SHGeoType.voxscore)
MEV_PER_GRAM_TO_GRAY = 1.602e-10


def bin_width(axis) -> float:
    """Width of a single bin of a linear mesh axis, in the axis unit (cm for SHIELD-HIT12A meshes)"""
    return (axis.max_val - axis.min_val) / axis.n


def check_mesh(estimator: Estimator) -> None:
    """Raise ValueError when the scoring mesh can not be stored in a TRiP98 cube header.

    TRiP98 cubes are cartesian, have a single pixel size for X and Y,
    and store the X and Y offsets as a whole number of pixels.
    """
    # bin2010 readers leave geotyp unset
    if estimator.geotyp is not None and estimator.geotyp not in CARTESIAN_GEOMETRIES:
        raise ValueError(f"TRiP98 cubes need a cartesian mesh, got {estimator.geotyp} geometry")

    x_bin_width = bin_width(estimator.x)
    y_bin_width = bin_width(estimator.y)
    if not np.isclose(x_bin_width, y_bin_width):
        raise ValueError(f"TRiP98 cubes have one pixel size for X and Y, "
                         f"got X bin width {x_bin_width:g} cm and Y bin width {y_bin_width:g} cm")

    for axis_name, axis in (("X", estimator.x), ("Y", estimator.y)):
        offset_in_pixels = axis.min_val / x_bin_width
        if not np.isclose(offset_in_pixels, np.rint(offset_in_pixels)):
            raise ValueError(f"TRiP98 cubes store the {axis_name} offset as a whole number of pixels, "
                             f"mesh starts at {axis.min_val:g} cm with {x_bin_width:g} cm pixels")


def page_skip_reason(page: Page) -> Optional[str]:
    """Explain why the page can not be written as a TRiP98 cube, None when it can"""
    if page.dettyp != SHDetType.dose and page.dettyp not in LET_TYPES:
        return f"{page.dettyp} page, only dose and LET pages can be written as TRiP98 cubes"
    if page.diff_axis1.n > 1 or page.diff_axis2.n > 1:
        return f"{page.dettyp} page has differential axes, TRiP98 cubes hold only X, Y and Z"
    return None


def dose_in_permille(estimator: Estimator, dose: np.ndarray) -> np.ndarray:
    """Convert dose to TRiP98 units, where 1000 is the planned dose.

    When the file carries the planned dose and number of primaries (bin2010 VOXSCORE files),
    dose in MeV/g per primary is scaled to the planned dose.
    Otherwise the dose is scaled so that its maximum is 1200.
    """
    if estimator.tripdose > 0.0 and estimator.tripntot > 0:
        dose_in_gray = dose * estimator.tripntot * MEV_PER_GRAM_TO_GRAY
        return dose_in_gray / estimator.tripdose * 1000.0
    return dose / dose.max() * 1200.0


class TRiP98CubeWriter(Writer):
    """Writes dose and LET pages as TRiP98 cubes, each page to its own .hed header and .dos data file"""

    def __init__(self, output_path: str, _):
        super().__init__(output_path)

    def write(self, estimator: Estimator) -> int:
        """Write every dose and LET page as a TRiP98 cube.

        Pages with other quantities or with differential axes are skipped with a warning.
        Raises ValueError when the mesh can not be stored in a TRiP98 cube or when no page can be written.
        """
        skip_reasons = []
        for page_number, page in enumerate(estimator.pages, start=1):
            skip_reason = page_skip_reason(page)
            if skip_reason is not None:
                skip_reasons.append(f"page {page_number}: {skip_reason}")
        if len(skip_reasons) == len(estimator.pages):
            raise ValueError("No page can be written as a TRiP98 cube; " + "; ".join(skip_reasons))

        check_mesh(estimator)

        return super().write(estimator)

    def write_single_page(self, page: Page, output_path: Path) -> None:
        """Write the page as a TRiP98 cube, dose as 16-bit integers (1000 = planned dose), LET in keV/um"""
        skip_reason = page_skip_reason(page)
        if skip_reason is not None:
            logger.warning("Skipping %s: %s", output_path, skip_reason)
            return

        try:
            from pytrip import __version__ as pytrip_version
            from pytrip import dos, let
        except ImportError as error:
            raise ImportError("pytrip package missing, to install type `pip install pytrip98`") from error

        if page.dettyp == SHDetType.dose:
            cube = dos.DosCube()
        else:
            cube = let.LETCube()

        # PyTRiP cube dimensions are in mm, SHIELD-HIT12A mesh in cm
        estimator = page.estimator
        if estimator is None:
            raise ValueError(f"Page {page.name} is not attached to an estimator")
        pixel_size = bin_width(estimator.x) * 10.0
        slice_distance = bin_width(estimator.z) * 10.0
        # TRiP98 offsets are the mesh edges for X and Y, slice positions are the slice centres
        first_slice_position = estimator.z.min_val * 10.0 + slice_distance / 2.0
        cube.create_empty_cube(1.0,
                               estimator.x.n,
                               estimator.y.n,
                               estimator.z.n,
                               pixel_size=pixel_size,
                               slice_distance=slice_distance,
                               xoffset=estimator.x.min_val * 10.0,
                               yoffset=estimator.y.min_val * 10.0,
                               slice_offset=first_slice_position)
        # without a z table the header has no slice positions and the Z offset is lost
        cube.z_table = True

        # page data is indexed (x, y, z), PyTRiP cubes are indexed (z, y, x)
        page_data_xyz = page.data[:, :, :, 0, 0]
        page_data_zyx = page_data_xyz.transpose()

        if page.dettyp == SHDetType.dose:
            cube.data_type = "integer"
            cube.num_bytes = 2
            cube.pydata_type = np.int16
            # PyTRiP truncates when casting to integers
            cube.cube = np.rint(dose_in_permille(estimator, page_data_zyx))
        else:
            cube.data_type = "float"
            cube.num_bytes = 4
            cube.pydata_type = np.float32
            cube.cube = page_data_zyx * 0.1  # MeV/cm -> keV/um

        cube.patient_name = "Anonymous"
        cube.created_by = getpass.getuser()
        cube.creation_info = f"Created with pymchelper {pymchelper.__version__}; using PyTRiP98 {pytrip_version}"

        logger.info("Writing page to: %s", str(output_path))
        cube.write(str(output_path))
