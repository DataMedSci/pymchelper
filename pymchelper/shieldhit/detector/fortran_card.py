from pymchelper.shieldhit.detector.geometry import Zone, Plane
from pymchelper.shieldhit.particle import SHParticleType


class CardLine:
    """
    Represents single line of detect.dat file
    """
    comment = "*----0---><----1---><----2---><----3---><----4---><----5---><----6--->"
    no_of_elements = 7
    element_length = 10

    def __init__(self, string_data):
        if len(string_data) != self.no_of_elements:
            raise Exception("Line should have {:d}, not {:d} elements".format(self.no_of_elements, len(string_data)))
        for element in string_data:
            if len(element) != self.element_length:
                raise Exception("Element [{:s}] should have {:d}, not {:d} elements".format(
                    element, self.element_length, len(element)))
        self.data = string_data

    def __str__(self):
        return "".join(self.data)

    @staticmethod
    def any_to_element(s):
        if len(str(s)) > CardLine.element_length:
            raise Exception("Element [{:s}] should have {:d}, not {:d} elements".format(
                str(s), CardLine.element_length, len(str(s))))
        if s is None:
            s = ""
        padding = " " * (CardLine.element_length - len(str(s)))
        return padding + str(s)


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
            tmp_heavy_ion = ["", estimator.heavy_ion_type.z, estimator.heavy_ion_type.a, "", "", "", ""]
            data_heavy_ion = [CardLine.any_to_element(d) for d in tmp_heavy_ion]
        if isinstance(estimator.geometry, Zone):
            data1_any = [
                estimator.estimator, estimator.geometry.start, estimator.geometry.stop, "",
                estimator.particle_type.value, estimator.detector_type, estimator.filename
            ]
            data1 = [CardLine.any_to_element(d) for d in data1_any]
            if estimator.particle_type == SHParticleType.heavy_ion:
                return CardLine(data1), CardLine(data_heavy_ion)
            return CardLine(data1)
        if isinstance(estimator.geometry, Plane):
            data1_any = [
                estimator.estimator, estimator.geometry.point_x, estimator.geometry.point_y, estimator.geometry.point_z,
                estimator.geometry.normal_x, estimator.geometry.normal_y, estimator.geometry.normal_z
            ]
            data1 = [CardLine.any_to_element(d) for d in data1_any]
            data2_any = ["", "", "", "", estimator.particle_type.value, estimator.detector_type, estimator.filename]
            data2 = [CardLine.any_to_element(d) for d in data2_any]
            if estimator.particle_type == SHParticleType.heavy_ion:
                return CardLine(data1), CardLine(data2), CardLine(data_heavy_ion)
            return CardLine(data1), CardLine(data2)
        data1_any = [
            estimator.estimator, estimator.geometry.axis[0].start, estimator.geometry.axis[1].start,
            estimator.geometry.axis[2].start, estimator.geometry.axis[0].stop, estimator.geometry.axis[1].stop,
            estimator.geometry.axis[2].stop
        ]
        data1 = [CardLine.any_to_element(d) for d in data1_any]
        data2_any = ["", estimator.geometry.axis[0].nbins, estimator.geometry.axis[1].nbins,
                     estimator.geometry.axis[2].nbins, estimator.particle_type.value, estimator.detector_type,
                     estimator.filename]
        data2 = [CardLine.any_to_element(d) for d in data2_any]
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
