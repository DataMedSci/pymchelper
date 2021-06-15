import logging

import numpy as np

from pymchelper.axis import MeshAxis
from pymchelper.page import Page
from pymchelper.readers.common import ReaderFactory, Reader
from pymchelper.flair.Data import Usrbin, UsrTrack, unpackArray, Usrbdx, Resnuclei, Usrxxx

logger = logging.getLogger(__name__)


class FlukaReaderFactory(ReaderFactory):
    """
    Class responsible for discovery of filetype.
    """
    def get_reader(self):
        """
        Try reading header of Fluka binary file and return a corresponding FlukaReader object

        :return: FlukaReader class if file is digested by Usrxxx Flair reader. None is returned otherwise
        """
        try:
            Usrxxx(self.filename)
            return FlukaReader
        except IOError:
            pass
        return None


class FlukaReader(Reader):

    @property
    def corename(self):
        """
        Fluka output filenames follow this pattern: corename_fort.XX.
        :return: corename part of output file or None in case filename doesn't follow Fluka naming pattern
        """
        core_name = None
        if "_fort" in self.filename:
            core_name = self.filename[-2:]
        return core_name

    def parse_usrbin(self, estimator):
        """
        USRBIN scores distribution of one of several quantities in a regular spatial
        structure (binning detector) independent from the geometry.
        :param estimator: an Estimator object, will be modified here and filled with data
        """
        try:
            usr_object = Usrbin(self.filename)

            # loop over all detectors (pages) in USRBIN object
            for det_no, detector in enumerate(usr_object.detector):
                page = Page(estimator=estimator)
                page.title = detector.name

                # USRBIN doesn't support differential binning type, only spatial binning is allowed
                estimator.x = MeshAxis(n=detector.nx,
                                       min_val=detector.xlow,
                                       max_val=detector.xhigh,
                                       name="X",
                                       unit="cm",
                                       binning=MeshAxis.BinningType.linear)
                estimator.y = MeshAxis(n=detector.ny,
                                       min_val=detector.ylow,
                                       max_val=detector.yhigh,
                                       name="Y",
                                       unit="cm",
                                       binning=MeshAxis.BinningType.linear)
                estimator.z = MeshAxis(n=detector.nz,
                                       min_val=detector.zlow,
                                       max_val=detector.zhigh,
                                       name="Z",
                                       unit="cm",
                                       binning=MeshAxis.BinningType.linear)

                page.name = "scorer {}".format(detector.score)
                page.unit = ""

                # unpack detector data
                # TODO cross-check if reshaping is needed
                page.data_raw = np.array(unpackArray(usr_object.readData(det_no)))
                page.error_raw = np.empty_like(page.data_raw)

                estimator.add_page(page)

            return usr_object
        except IOError:
            return None

    def parse_usrbdx(self, estimator):
        """
        USRBDX defines a detector for a boundary crossing fluence or current estimator
        :param estimator: an Estimator object, will be modified here and filled with data
        """
        try:
            usr_object = Usrbdx(self.filename)

            # loop over all detectors (pages) in USRBDX object
            for det_no, detector in enumerate(usr_object.detector):
                page = Page(estimator=estimator)
                page.title = detector.name
                page.area = detector.area  # area of the detector in cm**2

                if detector.nb == 1:
                    energy_binning = MeshAxis.BinningType.linear
                    angle_binning = MeshAxis.BinningType.linear
                elif detector.nb == -1:
                    energy_binning = MeshAxis.BinningType.logarithmic
                    angle_binning = MeshAxis.BinningType.linear
                elif detector.nb == 2:
                    energy_binning = MeshAxis.BinningType.linear
                    angle_binning = MeshAxis.BinningType.logarithmic
                elif detector.nb == -2:
                    energy_binning = MeshAxis.BinningType.logarithmic
                    angle_binning = MeshAxis.BinningType.logarithmic
                else:
                    return Exception("Invalid binning type")

                # USRBDX doesn't support spatial (XYZ) binning type
                # USRBDX provides double differential binning, first axis is kinetic energy (in GeV)
                page.diff_axis1 = MeshAxis(n=detector.ne,  # number of energy intervals for scoring
                                           min_val=detector.elow,  # minimum kinetic energy for scoring (GeV)
                                           max_val=detector.ehigh,  # maximum kinetic energy for scoring (GeV)
                                           name="kinetic energy",
                                           unit="GeV",
                                           binning=energy_binning)

                # second axis is solid angle (in steradians)
                page.diff_axis2 = MeshAxis(n=detector.na,  # number of angular bins
                                           min_val=detector.alow,  # minimum solid angle for scoring
                                           max_val=detector.ahigh,  # maximum solid angle for scoring
                                           name="solid angle",
                                           unit="sr",
                                           binning=angle_binning)

                # detector.fluence corresponds to i2 in WHAT(1) in first card of USBDX
                if detector.fluence == 1:
                    page.name = "fluence"
                elif detector.fluence == 0:
                    page.name = "current"
                else:
                    page.name = ""
                page.unit = "cm-2 GeV-1 sr-1"

                # TODO If the generalised particle is 208.0 (ENERGY) or 211.0 (EM-ENRGY),
                #             the quantity scored is differential energy fluence (if
                #             cosine-weighted) or differential energy current (energy crossing the
                #             surface). In both cases the quantity will be expressed in GeV per
                #             cm2 per energy unit per steradian per primary

                # unpack detector data
                # TODO cross-check if reshaping is needed
                page.data_raw = np.array(unpackArray(usr_object.readData(det_no)))
                page.error_raw = np.empty_like(page.data_raw)

                estimator.add_page(page)

            return usr_object
        except IOError:
            return None

    def parse_usrtrack(self, estimator):
        """
        :param estimator: an Estimator object, will be modified here and filled with data
        USRTRACK defines a detector for a track-length fluence estimator
        """
        try:
            usr_object = UsrTrack(self.filename)

            # loop over all detectors (pages) in USRTRACK object
            for det_no, detector in enumerate(usr_object.detector):
                page = Page(estimator=estimator)
                page.title = detector.name
                page.volume = detector.volume   # volume of the detector in cm**3

                # USRTRACK doesn't support spatial (XYZ) binning type
                if detector.type == 1:
                    energy_binning = MeshAxis.BinningType.linear
                elif detector.type == -1:
                    energy_binning = MeshAxis.BinningType.logarithmic
                else:
                    return Exception("Invalid binning type")

                # USRTRACK provides single differential binning, with diff axis in kinetic energy (in GeV)
                page.diff_axis1 = MeshAxis(n=detector.ne,  # number of energy intervals for scoring
                                           min_val=detector.elow,  # minimum kinetic energy for scoring (GeV)
                                           max_val=detector.ehigh,  # maximum kinetic energy for scoring (GeV)
                                           name="kinetic energy",
                                           unit="GeV",
                                           binning=energy_binning)

                page.name = "fluence"
                page.unit = "cm-2 GeV-1"

                # TODO IMPORTANT! The results of USRTRACK are always given as DIFFERENTIAL
                #             distributions of fluence (or tracklength, if the detector region
                #             volume is not specified) in energy, in units of cm-2 GeV-1 (or
                #             cm GeV-1) per incident primary unit weight. Thus, for example, when
                #             requesting a fluence energy spectrum, to obtain INTEGRAL BINNED
                #             results (fluence in cm-2 or tracklength in cm PER ENERGY BIN per
                #             primary) one must multiply the value of each energy bin by the width
                #             of the bin (even for logarithmic binning)

                # TODO If the generalised particle is 208 (ENERGY) or 211 (EM-ENRGY), the
                #             quantity scored is differential energy fluence (or tracklength, if
                #             the detector region volume is not specified), expressed in GeV per
                #             cm2 (or cm GeV) per energy unit per primary. That can sometimes lead
                #             to confusion since GeV cm-2 GeV-1 = cm-2, where energy does not appear.
                #             Note that integrating over energy one gets GeV/cm2.

                # unpack detector data
                # TODO cross-check if reshaping is needed
                page.data_raw = np.array(unpackArray(usr_object.readData(det_no)))
                page.error_raw = np.empty_like(page.data_raw)

                estimator.add_page(page)
            return usr_object
        except IOError:
            return None

    def parse_resnuclei(self, estimator):
        """
        TODO add support for resnuclei
        RESNUCLEi Scores residual nuclei produced in inelastic interactions on a region basis
        :param estimator: an Estimator object, will be modified here and filled with data
        """
        try:
            usr_object = Resnuclei(self.filename)
            # loop over all detectors (pages) in USRTRACK object
            for det_no, detector in enumerate(usr_object.detector):
                page = Page(estimator=estimator)

                # unpack detector data
                # TODO cross-check if reshaping is needed
                page.data_raw = np.array(unpackArray(usr_object.readData(det_no)))
                page.error_raw = np.empty_like(page.data_raw)

                estimator.add_page(page)
            return usr_object
        except IOError:
            return None

    def parse_data(self, estimator):
        """
        TODO
        :param estimator: an Estimator object, will be modified here and filled with data
        """
        for parse_function in (self.parse_usrbin, self.parse_usrtrack, self.parse_usrbdx, self.parse_resnuclei):
            usr_object = parse_function(estimator)

            # stop on first method which return not-None results and return it back
            if usr_object:
                return usr_object

    def read_data(self, estimator, nscale=1):
        """
        TODO
        :param estimator: an Estimator object, will be modified here and filled with data
        """
        usr_object = self.parse_data(estimator)

        estimator.file_counter = usr_object.nbatch
        estimator.number_of_primaries = usr_object.ncase
        estimator.time = usr_object.time
        estimator.title = usr_object.title

        estimator.file_format = 'fluka_binary'
        return True
