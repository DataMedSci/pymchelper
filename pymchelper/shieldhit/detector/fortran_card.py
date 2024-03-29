from pymchelper.shieldhit.detector.estimator_type import SHGeoType
from pymchelper.shieldhit.detector.geometry import Zone, Plane
from pymchelper.shieldhit.particle import SHParticleType


class CardLine:
    """
    Represents single line of detect.dat file
    """

    comment = "*----0---><----1---><----2---><----3---><----4---><----5---><----6--->"
    credits = "* generated by pymchelper (https://github.com/DataMedSci/pymchelper) *"
    no_of_elements = 7
    element_length = 10

    def __init__(self, data=None):
        self.data = []
        if data is None:
            self.data = [" " * CardLine.element_length] * CardLine.no_of_elements
        else:
            for element in data:
                if isinstance(element, SHGeoType):
                    elem_string = CardLine.any_to_element(element, align_right=False)
                else:
                    elem_string = CardLine.any_to_element(element)
                self.data.append(elem_string)

    def __str__(self):
        return "".join(self.data)

    @staticmethod
    def any_to_element(s, align_right=True):
        if len(str(s)) > CardLine.element_length:
            raise Exception("Element [{:s}] should have {:d}, not {:d} elements".format(
                str(s), CardLine.element_length, len(str(s))))
        if s is None:
            s = ""
        padding = " " * (CardLine.element_length - len(str(s)))
        result = padding + str(s)
        if not align_right:
            result = str(s) + padding
        return result


class EstimatorWriter:
    """
    Helper class. Gives textual representation of Estimator objects.
    """

    @staticmethod
    def get_lines(estimator):
        """
        Converts estimator to CardLine objects
        :param estimator: valid estimator object
        :return: tuple of CardLine objects
        """
        if estimator.particle_type == SHParticleType.heavy_ion:
            data_heavy_ion = ["", estimator.heavy_ion_type.z, estimator.heavy_ion_type.a, "", "", "", ""]
        if isinstance(estimator.geometry, Zone):
            data1 = [
                estimator.estimator, estimator.geometry.start, estimator.geometry.stop, "",
                estimator.particle_type.value, estimator.detector_type, estimator.filename
            ]
            if estimator.particle_type == SHParticleType.heavy_ion:
                return CardLine(data1), CardLine(data_heavy_ion)
            return (CardLine(data1),)
        if isinstance(estimator.geometry, Plane):
            data1 = [
                estimator.estimator, estimator.geometry.point_x, estimator.geometry.point_y, estimator.geometry.point_z,
                estimator.geometry.normal_x, estimator.geometry.normal_y, estimator.geometry.normal_z
            ]
            data2 = ["", "", "", "", estimator.particle_type.value, estimator.detector_type, estimator.filename]
            if estimator.particle_type == SHParticleType.heavy_ion:
                return CardLine(data1), CardLine(data2), CardLine(data_heavy_ion)
            return CardLine(data1), CardLine(data2)
        data1 = [
            estimator.estimator, estimator.geometry.axis[0].start, estimator.geometry.axis[1].start,
            estimator.geometry.axis[2].start, estimator.geometry.axis[0].stop, estimator.geometry.axis[1].stop,
            estimator.geometry.axis[2].stop
        ]
        data2 = ["", estimator.geometry.axis[0].nbins, estimator.geometry.axis[1].nbins,
                 estimator.geometry.axis[2].nbins, estimator.particle_type.value, estimator.detector_type,
                 estimator.filename]
        if estimator.particle_type == SHParticleType.heavy_ion:
            return CardLine(data1), CardLine(data2), CardLine(data_heavy_ion)
        return CardLine(data1), CardLine(data2)

    @staticmethod
    def get_text(estimator, add_comment=False):
        """
        Converts Estimator to text
        :param estimator: valid Estimator object
        :param add_comment: if True, prepends textual representation with comment line
        :return: text representation (set of text lines) of Estimator
        """
        code_lines = EstimatorWriter.get_lines(estimator)
        result = ""
        if add_comment:
            result = CardLine.comment + "\n"
        result += "\n".join(map(str, code_lines)) + "\n"
        return result


class EstimatorReader:
    pass
    # TODO to be implemented
