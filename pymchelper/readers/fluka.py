import logging

import numpy as np

from pymchelper.estimator import MeshAxis
from pymchelper.readers.common import ReaderFactory, Reader
from pymchelper.shieldhit.detector.detector_type import SHDetType
from pymchelper.shieldhit.detector.estimator_type import SHGeoType
from pymchelper.flair.Data import Usrbin, UsrTrack, unpackArray

logger = logging.getLogger(__name__)


class FlukaReaderFactory(ReaderFactory):
    def get_reader(self):
        if "_fort" in self.filename:
            return FlukaReader
        return None


class FlukaReader(Reader):

    @property
    def corename(self):
        core_name = None
        if "_fort" in self.filename:
            core_name = self.filename[-2:]
        return core_name

    def read_data(self, estimator, nscale=1):

        try:
            usr = Usrbin(self.filename)
            data = usr.readData(0)
            fdata = unpackArray(data)
        except IOError:
            usr = UsrTrack(self.filename)
            data = usr.readData(0)
            fdata = unpackArray(data)[:usr.detector[0].ne]
        usr.say()  # file,title,time,weight,ncase,nbatch
        for i, _ in enumerate(usr.detector):
            logger.debug("-" * 20 + (" Detector number %i " % i) + "-" * 20)
            usr.say(i)  # details for each detector

        # TODO read detector type
        estimator.det = "FLUKA"

        # TODO read particle type
        estimator.particle = 0

        # TODO read geo type
        estimator.geotyp = SHGeoType.unknown

        # TODO cross-check statistics
        estimator.number_of_primaries = usr.ncase

        # TODO figure out when more detectors are used
        nx = usr.detector[0].nx
        ny = usr.detector[0].ny
        nz = usr.detector[0].nz

        xmin = usr.detector[0].xlow
        ymin = usr.detector[0].ylow
        zmin = usr.detector[0].zlow

        xmax = usr.detector[0].xhigh
        ymax = usr.detector[0].yhigh
        zmax = usr.detector[0].zhigh

        estimator.x = MeshAxis(n=nx, min_val=xmin, max_val=xmax,
                               name="X", unit="", binning=MeshAxis.BinningType.linear)
        estimator.y = MeshAxis(n=ny, min_val=ymin, max_val=ymax,
                               name="Y", unit="", binning=MeshAxis.BinningType.linear)
        estimator.z = MeshAxis(n=nz, min_val=zmin, max_val=zmax,
                               name="Z", unit="", binning=MeshAxis.BinningType.linear)

        estimator.pages[0].unit, estimator.pages[0].name = "", ""

        # TODO read detector type
        estimator.pages[0].dettyp = SHDetType.none  # TODO replace with Fluka detector type

        estimator.pages[0].data_raw = np.array(fdata)
        if nscale != 1:
            estimator.pages[0].data_raw *= nscale
            # 1 gigaelectron volt / gram = 1.60217662 x 10-7 Gy
            estimator.pages[0].data_raw *= 1.60217662e-7

        estimator.title = usr.detector[0].name.decode('ascii')
        return True
