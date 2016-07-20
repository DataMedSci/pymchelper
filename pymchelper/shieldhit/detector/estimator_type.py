from enum import IntEnum


class SHGeoType(IntEnum):
    unknown = 0
    zone = 1
    cyl = 2
    msh = 3
    plane = 4
    dzone = 5
    dcyl = 6
    dmsh = 7
    dplane = 8
    dcylz = 10
    dmshz = 11
    trace = 13
    voxscore = 14
    geomap = 15

    def __str__(self):
        return self.name.upper()
