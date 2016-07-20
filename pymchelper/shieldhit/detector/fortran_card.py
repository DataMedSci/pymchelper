class CardLine:
    comment = "*----0---><----1---><----2---><----3--->" \
              "<----4---><----5---><----6--->"
    no_of_elements = 7
    element_length = 10

    def __init__(self, string_data):
        if len(string_data) != self.no_of_elements:
            raise Exception("Line should have {:d}, not {:d} elements".format(
                self.no_of_elements, len(string_data)))
        for element in string_data:
            if len(element) != self.element_length:
                raise Exception("Element [{:s}] should have {:d}, "
                                "not {:d} elements".format(element,
                                                           self.element_length,
                                                           len(element)))
        self.data = string_data

    def __str__(self):
        return "".join(self.data)

    @staticmethod
    def number_to_element(n):
        if len(str(n)) > CardLine.element_length:
            raise Exception("Element [{:s}] should have {:d}, "
                            "not {:d} elements".format(str(n),
                                                       CardLine.element_length,
                                                       len(str(n))))
        padding = " " * (CardLine.element_length - len(str(n)))
        result = padding + str(n)
        return result

    @staticmethod
    def string_to_element(s):
        if len(s) > CardLine.element_length:
            raise Exception("Element [{:s}] should have {:d}, "
                            "not {:d} elements".format(s,
                                                       CardLine.element_length,
                                                       len(s)))
        padding = " " * (CardLine.element_length - len(s))
        return padding + s

    @staticmethod
    def any_to_element(a):
        if type(a) is str:
            return CardLine.string_to_element(a)
        else:
            return CardLine.number_to_element(a)


class EstimatorWriter:
    @classmethod
    def write(self, estimator):
        data1_any = [estimator.estimator,
                     estimator.geometry.axis[0].start,
                     estimator.geometry.axis[1].start,
                     estimator.geometry.axis[2].start,
                     estimator.geometry.axis[0].stop,
                     estimator.geometry.axis[1].stop,
                     estimator.geometry.axis[2].stop]
        data1 = [CardLine.any_to_element(d) for d in data1_any]
        data2_any = ["",
                     estimator.geometry.axis[0].nbins,
                     estimator.geometry.axis[1].nbins,
                     estimator.geometry.axis[2].nbins,
                     estimator.particle_type.value,
                     estimator.detector_type,
                     estimator.filename]
        data2 = [CardLine.any_to_element(d) for d in data2_any]
        return CardLine(data1), CardLine(data2)


class EstimatorReader:
    pass
