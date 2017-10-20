import logging

import numpy as np

from pymchelper.detector import MeshAxis
from pymchelper.shieldhit.detector.detector_type import SHDetType
from pymchelper.shieldhit.detector.estimator_type import SHGeoType
from pymchelper.flair.Data import Usrbin, UsrTrack, unpackArray

logger = logging.getLogger(__name__)


class FlukaBinaryReader:
    def __init__(self, filename):
        self.filename = filename

    def read(self, detector, nscale=1):

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
        detector.det = "FLUKA"

        # TODO read particle type
        detector.particle = 0

        # TODO read geo type
        detector.geotyp = SHGeoType.unknown

        # TODO cross-check statistics
        detector.nstat = usr.ncase

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

        detector.x = MeshAxis(n=nx, min_val=xmin, max_val=xmax,
                              name="X", unit="", binning=MeshAxis.BinningType.linear)
        detector.y = MeshAxis(n=ny, min_val=ymin, max_val=ymax,
                              name="Y", unit="", binning=MeshAxis.BinningType.linear)
        detector.z = MeshAxis(n=nz, min_val=zmin, max_val=zmax,
                              name="Z", unit="", binning=MeshAxis.BinningType.linear)

        detector.unit, detector.name = "", ""

        # TODO read detector type
        detector.dettyp = SHDetType.unknown

        detector.data_raw = np.array(fdata)
        if nscale != 1:
            detector.data *= nscale
            # 1 gigaelectron volt / gram = 1.60217662 x 10-7 Gy
            detector.data *= 1.60217662e-7

        detector.title = usr.detector[0].name.decode('ascii')
