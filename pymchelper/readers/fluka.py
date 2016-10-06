import logging

import numpy as np

from pymchelper.shieldhit.detector.detector_type import SHDetType
from pymchelper.shieldhit.detector.estimator_type import SHGeoType
from pymchelper.flair.Data import Usrbin, unpackArray

logger = logging.getLogger(__name__)


class FlukaBinaryReader:
    def __init__(self, filename):
        self.filename = filename

    def read(self, detector):
        usr = Usrbin(self.filename)
        usr.say()  # file,title,time,weight,ncase,nbatch
        for i, _ in enumerate(usr.detector):
            logger.debug("-" * 20 + (" Detector number %i " % i) + "-" * 20)
            usr.say(i)  # details for each detector
        data = usr.readData(0)
        fdata = unpackArray(data)

        # TODO read detector type
        detector.det = "FLUKA"

        # TODO read particle type
        detector.particle = 0

        # TODO read geo type
        detector.geotyp = SHGeoType.unknown

        # TODO cross-check statistics
        detector.nstat = usr.ncase

        # TODO figure out when more detectors are used
        detector.nx = usr.detector[0].nx
        detector.ny = usr.detector[0].ny
        detector.nz = usr.detector[0].nz

        detector.xmin = usr.detector[0].xlow
        detector.ymin = usr.detector[0].ylow
        detector.zmin = usr.detector[0].zlow

        detector.xmax = usr.detector[0].xhigh
        detector.ymax = usr.detector[0].yhigh
        detector.zmax = usr.detector[0].zhigh

        # TODO read detector type
        detector.dettyp = SHDetType.unknown

        detector.data = np.array(fdata)

        # set units : detector.units are [x,y,z,v,data,detector_title]
        detector.units = [""] * 6
