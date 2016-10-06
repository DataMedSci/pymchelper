#!/bin/env python
# $Id: Data.py 3608 2015-10-27 11:18:36Z bnv $
#
# Copyright and User License
# ~~~~~~~~~~~~~~~~~~~~~~~~~~
# Copyright Vasilis.Vlachoudis@cern.ch for the
# European Organization for Nuclear Research (CERN)
#
# All rights not expressly granted under this license are reserved.
#
# Installation, use, reproduction, display of the
# software ("flair"), in source and binary forms, are
# permitted free of charge on a non-exclusive basis for
# internal scientific, non-commercial and non-weapon-related
# use by non-profit organizations only.
#
# For commercial use of the software, please contact the main
# author Vasilis.Vlachoudis@cern.ch for further information.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following
# conditions are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the
#    distribution.
#
# DISCLAIMER
# ~~~~~~~~~~
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT
# NOT LIMITED TO, IMPLIED WARRANTIES OF MERCHANTABILITY, OF
# SATISFACTORY QUALITY, AND FITNESS FOR A PARTICULAR PURPOSE
# OR USE ARE DISCLAIMED. THE COPYRIGHT HOLDERS AND THE
# AUTHORS MAKE NO REPRESENTATION THAT THE SOFTWARE AND
# MODIFICATIONS THEREOF, WILL NOT INFRINGE ANY PATENT,
# COPYRIGHT, TRADE SECRET OR OTHER PROPRIETARY RIGHT.
#
# LIMITATION OF LIABILITY
# ~~~~~~~~~~~~~~~~~~~~~~~
# THE COPYRIGHT HOLDERS AND THE AUTHORS SHALL HAVE NO
# LIABILITY FOR DIRECT, INDIRECT, SPECIAL, INCIDENTAL,
# CONSEQUENTIAL, EXEMPLARY, OR PUNITIVE DAMAGES OF ANY
# CHARACTER INCLUDING, WITHOUT LIMITATION, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES, LOSS OF USE, DATA OR PROFITS,
# OR BUSINESS INTERRUPTION, HOWEVER CAUSED AND ON ANY THEORY
# OF CONTRACT, WARRANTY, TORT (INCLUDING NEGLIGENCE), PRODUCT
# LIABILITY OR OTHERWISE, ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGES.
#
# Author:	Vasilis.Vlachoudis@cern.ch
# Date:	24-Oct-2006

import re
import math
import struct

import pymchelper.flair.common.fortran as fortran
import pymchelper.flair.common.bmath as bmath
from pymchelper.flair.common.log import say

__author__ = "Vasilis Vlachoudis"
__email__ = "Vasilis.Vlachoudis@cern.ch"

_detectorPattern = re.compile(r"^ ?# ?Detector ?n?:\s*\d*\s*(.*)\s*", re.MULTILINE)
_blockPattern = re.compile(r"^ ?# ?Block ?n?:\s*\d*\s*(.*)\s*", re.MULTILINE)


# -------------------------------------------------------------------------------
# Unpack an array of floating point numbers
# -------------------------------------------------------------------------------
def unpackArray(data):
    return struct.unpack("=%df" % (len(data) // 4), data)


# ===============================================================================
# Empty class to fill with detector data
# ===============================================================================
class Detector:
    pass


# ===============================================================================
# Base class for all detectors
# ===============================================================================
class Usrxxx:
    def __init__(self, filename=None):
        """Initialize a USRxxx structure"""
        self.reset()
        if filename is None:
            return
        f = self.readHeader(filename)
        if f is not None and not f.closed:
            f.close()

    # ----------------------------------------------------------------------
    def reset(self):
        """Reset header information"""
        self.file = ""
        self.title = ""
        self.time = ""
        self.weight = 0
        self.ncase = 0
        self.nbatch = 0
        self.detector = []
        self.seekpos = -1
        self.statpos = -1

    # ----------------------------------------------------------------------
    # Read information from USRxxx file
    # @return the handle to the file opened
    # ----------------------------------------------------------------------
    def readHeader(self, filename):
        """Read header information, and return the file handle"""
        self.reset()
        self.file = filename
        f = open(self.file, "rb")

        # Read header
        data = fortran.read(f)
        if data is None:
            if not f.closed:
                f.close()
            raise IOError("Invalid USRxxx file")
        size = len(data)
        over1b = 0
        if size == 116:
            (title, time, self.weight) = \
                struct.unpack("=80s32sf", data)
            self.ncase = 1
            self.nbatch = 1
        elif size == 120:
            (title, time, self.weight, self.ncase) = \
                struct.unpack("=80s32sfi", data)
            self.nbatch = 1
        elif size == 124:
            (title, time, self.weight,
             self.ncase, self.nbatch) = \
                struct.unpack("=80s32sfii", data)
        elif size == 128:
            (title, time, self.weight,
             self.ncase, over1b, self.nbatch) = \
                struct.unpack("=80s32sfiii", data)
        else:
            if not f.closed:
                f.close()
            raise IOError("Invalid USRxxx file")

        if over1b > 0:
            self.ncase = int(self.ncase) + int(over1b) * 1000000000

        self.title = title.strip()
        self.time = time.strip()

        return f

    # ----------------------------------------------------------------------
    # Read detector data
    # ----------------------------------------------------------------------
    def readData(self, det):
        """Read detector det data structure"""
        f = open(self.file, "rb")
        fortran.skip(f)  # Skip header
        for i in range(2 * det):
            fortran.skip(f)  # Detector Header & Data
        fortran.skip(f)  # Detector Header
        data = fortran.read(f)
        f.close()
        return data

    # ----------------------------------------------------------------------
    # Read detector statistical data
    # ----------------------------------------------------------------------
    def readStat(self, det):
        """Read detector det statistical data"""
        if self.statpos < 0:
            return None
        f = open(self.file, "rb")
        f.seek(self.statpos)
        for _ in range(det):
            fortran.skip(f)  # Detector Data
        data = fortran.read(f)
        f.close()
        return data

    # ----------------------------------------------------------------------
    def sayHeader(self):
        say("File   : ", self.file)
        say("Title  : ", self.title)
        say("Time   : ", self.time)
        say("Weight : ", self.weight)
        say("NCase  : ", self.ncase)
        say("NBatch : ", self.nbatch)


# ===============================================================================
# Residual nuclei detector
# ===============================================================================
class Resnuclei(Usrxxx):
    # ----------------------------------------------------------------------
    # Read information from a RESNUCLEi file
    # Fill the self.detector structure
    # ----------------------------------------------------------------------
    def readHeader(self, filename):
        """Read residual nuclei detector information"""
        f = Usrxxx.readHeader(self, filename)
        self.nisomers = 0
        if self.ncase <= 0:
            self.evol = True
            self.ncase = -self.ncase

            data = fortran.read(f)
            nir = (len(data) - 4) // 8
            self.irrdt = struct.unpack("=i%df" % (2 * nir), data)
        else:
            self.evol = False
            self.irrdt = None

        for _ in range(1000):
            # Header
            data = fortran.read(f)
            if data is None:
                break
            size = len(data)
            self.irrdt = None

            # Statistics are present?
            if size == 14 and data[:8] == "ISOMERS:":
                self.nisomers = struct.unpack("=10xi", data)[0]
                data = fortran.read(f)
                data = fortran.read(f)
                size = len(data)

            if size == 14 and data[:10] == "STATISTICS":
                self.statpos = f.tell()
                break

            if size != 38:
                if not f.closed:
                    f.close()
                raise IOError("Invalid RESNUCLEi file header size=%d" % (size))

            # Parse header
            header = struct.unpack("=i10siif3i", data)

            det = Detector()
            det.nb = header[0]
            det.name = header[1].strip()
            det.type = header[2]
            det.region = header[3]
            det.volume = header[4]
            det.mhigh = header[5]
            det.zhigh = header[6]
            det.nmzmin = header[7]

            self.detector.append(det)

            if self.evol:
                data = fortran.read(f)
                self.tdecay = struct.unpack("=f", data)
            else:
                self.tdecay = 0.0

            size = det.zhigh * det.mhigh * 4
            if size != fortran.skip(f):
                raise IOError("Invalid RESNUCLEi file")

        f.close()

    # ----------------------------------------------------------------------
    # Read detector data
    # ----------------------------------------------------------------------
    def readData(self, n):
        """Read detector det data structure"""
        f = open(self.file, "rb")
        fortran.skip(f)
        if self.evol:
            fortran.skip(f)

        for _ in range(n):
            fortran.skip(f)  # Detector Header & Data
            if self.evol:
                fortran.skip(f)  # TDecay
            fortran.skip(f)  # Detector data
            if self.nisomers:
                fortran.skip(f)  # Isomers header
                fortran.skip(f)  # Isomers data

        fortran.skip(f)  # Detector Header & Data
        if self.evol:
            fortran.skip(f)  # TDecay
        data = fortran.read(f)  # Detector data
        f.close()
        return data

    # ----------------------------------------------------------------------
    # Read detector statistical data
    # ----------------------------------------------------------------------
    def readStat(self, n):
        """Read detector det statistical data"""
        if self.statpos < 0:
            return None
        f = open(self.file, "rb")
        f.seek(self.statpos)

        f.seek(self.statpos)
        if self.nisomers:
            nskip = 7 * n
        else:
            nskip = 6 * n
        for i in range(nskip):
            fortran.skip(f)  # Detector Data

        total = fortran.read(f)
        A = fortran.read(f)
        errA = fortran.read(f)
        Z = fortran.read(f)
        errZ = fortran.read(f)
        data = fortran.read(f)
        if self.nisomers:
            iso = fortran.read(f)
        else:
            iso = None
        f.close()
        return (total, A, errA, Z, errZ, data, iso)

    # ----------------------------------------------------------------------
    def say(self, det=None):
        """print header/detector information"""
        if det is None:
            self.sayHeader()
        else:
            bin = self.detector[det]
            say("Bin    : ", bin.nb)
            say("Title  : ", bin.name)
            say("Type   : ", bin.type)
            say("Region : ", bin.region)
            say("Volume : ", bin.volume)
            say("Mhigh  : ", bin.mhigh)
            say("Zhigh  : ", bin.zhigh)
            say("NMZmin : ", bin.nmzmin)


# ===============================================================================
# Usrbdx Boundary Crossing detector
# ===============================================================================
class Usrbdx(Usrxxx):
    # ----------------------------------------------------------------------
    # Read information from a USRBDX file
    # Fill the self.detector structure
    # ----------------------------------------------------------------------
    def readHeader(self, filename):
        """Read boundary crossing detector information"""
        f = Usrxxx.readHeader(self, filename)

        for _ in range(1000):
            # Header
            data = fortran.read(f)
            if data is None:
                break
            size = len(data)

            # Statistics are present?
            if size == 14:
                # In statistics
                #   1: total, error
                #   2: N,NG,Elow (array with Emaxi)
                #   3: Differential integrated over solid angle
                #   4: -//- errors
                #   5: Cumulative integrated over solid angle
                #   6: -//- errors
                #   7: Double differential data
                self.statpos = f.tell()
                for det in self.detector:
                    data = unpackArray(fortran.read(f))
                    det.total = data[0]
                    det.totalerror = data[1]
                    for j in range(6):
                        fortran.skip(f)
                break
            if size != 78:
                if not f.closed:
                    f.close()
                raise IOError("Invalid USRBDX file")

            # Parse header
            header = struct.unpack("=i10siiiifiiiffifffif", data)

            det = Detector()
            det.nb = header[0]  # mx
            det.name = header[1].strip()  # titusx
            det.type = header[2]  # itusbx
            det.dist = header[3]  # idusbx
            det.reg1 = header[4]  # nr1usx
            det.reg2 = header[5]  # nr2usx
            det.area = header[6]  # ausbdx
            det.twoway = header[7]  # lwusbx
            det.fluence = header[8]  # lfusbx
            det.lowneu = header[9]  # llnusx
            det.elow = header[10]  # ebxlow
            det.ehigh = header[11]  # ebxhgh
            det.ne = header[12]  # nebxbn
            det.de = header[13]  # debxbn
            det.alow = header[14]  # abxlow
            det.ahigh = header[15]  # abxhgh
            det.na = header[16]  # nabxbn
            det.da = header[17]  # dabxbn

            self.detector.append(det)

            if det.lowneu:
                data = fortran.read(f)
                det.ngroup = struct.unpack("=i", data[:4])[0]
                det.egroup = struct.unpack("=%df" % (det.ngroup + 1), data[4:])
            else:
                det.ngroup = 0
                det.egroup = []

            size = (det.ngroup + det.ne) * det.na * 4
            if size != fortran.skip(f):
                raise IOError("Invalid USRBDX file")
        f.close()

    # ----------------------------------------------------------------------
    # Read detector data
    # ----------------------------------------------------------------------
    def readData(self, n):
        """Read detector n data structure"""
        f = open(self.file, "rb")
        fortran.skip(f)
        for i in range(n):
            fortran.skip(f)  # Detector Header
            if self.detector[i].lowneu:
                fortran.skip(f)  # Detector low enetry neutron groups
            fortran.skip(f)  # Detector data

        fortran.skip(f)  # Detector Header
        if self.detector[n].lowneu:
            fortran.skip(f)  # Detector low enetry neutron groups
        data = fortran.read(f)  # Detector data
        f.close()
        return data

    # ----------------------------------------------------------------------
    # Read detector statistical data
    # ----------------------------------------------------------------------
    def readStat(self, n):
        """Read detector n statistical data"""
        if self.statpos < 0:
            return None
        f = open(self.file, "rb")
        f.seek(self.statpos)
        for i in range(n):
            for j in range(7):
                fortran.skip(f)  # Detector Data

        for j in range(6):
            fortran.skip(f)  # Detector Data
        data = fortran.read(f)
        f.close()
        return data

    # ----------------------------------------------------------------------
    def say(self, det=None):
        """print header/detector information"""
        if det is None:
            self.sayHeader()
        else:
            det = self.detector[det]
            say("BDX    : ", det.nb)
            say("Title  : ", det.name)
            say("Type   : ", det.type)
            say("Dist   : ", det.dist)
            say("Reg1   : ", det.reg1)
            say("Reg2   : ", det.reg2)
            say("Area   : ", det.area)
            say("2way   : ", det.twoway)
            say("Fluence: ", det.fluence)
            say("LowNeu : ", det.lowneu)
            say("Energy : [", det.elow, "..", det.ehigh, "] ne=", det.ne, "de=", det.de)
            if det.lowneu:
                say("LOWNeut : [", det.egroup[-1], "..", det.egroup[0], "] ne=", det.ngroup)
            say("Angle  : [", det.alow, "..", det.ahigh, "] na=", det.na, "da=", det.da)
            say("Total  : ", det.total, "+/-", det.totalerror)


# ===============================================================================
# Usrbin detector
# ===============================================================================
class Usrbin(Usrxxx):
    # ----------------------------------------------------------------------
    # Read information from USRBIN file
    # Fill the self.detector structure
    # ----------------------------------------------------------------------
    def readHeader(self, filename):
        """Read USRBIN detector information"""
        f = Usrxxx.readHeader(self, filename)

        for _ in range(1000):
            # Header
            data = fortran.read(f)
            if data is None:
                break
            size = len(data)

            # Statistics are present?
            if size == 14 and data[:10] == "STATISTICS":
                self.statpos = f.tell()
                break
            if size != 86:
                if not f.closed:
                    f.close()
                raise IOError("Invalid USRBIN file")

            # Parse header
            header = struct.unpack("=i10siiffifffifffififff", data)

            bin_det = Detector()
            bin_det.nb = header[0]
            bin_det.name = header[1].strip()
            bin_det.type = header[2]
            bin_det.score = header[3]

            bin_det.xlow = float(bmath.format_number(header[4], 9, useD=False))
            bin_det.xhigh = float(bmath.format_number(header[5], 9, useD=False))
            bin_det.nx = header[6]
            if bin_det.nx > 0 and bin_det.type not in (2, 12, 8, 18):
                bin_det.dx = (bin_det.xhigh - bin_det.xlow) / float(bin_det.nx)
            else:
                bin_det.dx = float(bmath.format_number(header[7], 9, useD=False))

            if bin_det.type in (1, 11):
                bin_det.ylow = -math.pi
                bin_det.yhigh = math.pi
            else:
                bin_det.ylow = float(bmath.format_number(header[8], 9, useD=False))
                bin_det.yhigh = float(bmath.format_number(header[9], 9, useD=False))
            bin_det.ny = header[10]
            if bin_det.ny > 0 and bin_det.type not in (2, 12, 8, 18):
                bin_det.dy = (bin_det.yhigh - bin_det.ylow) / float(bin_det.ny)
            else:
                bin_det.dy = float(bmath.format_number(header[11], 9, useD=False))

            bin_det.zlow = float(bmath.format_number(header[12], 9, useD=False))
            bin_det.zhigh = float(bmath.format_number(header[13], 9, useD=False))
            bin_det.nz = header[14]
            if bin_det.nz > 0 and bin_det.type not in (2, 12):  # 8=special with z=real
                bin_det.dz = (bin_det.zhigh - bin_det.zlow) / float(bin_det.nz)
            else:
                bin_det.dz = float(bmath.format_number(header[15], 9, useD=False))

            bin_det.lntzer = header[16]
            bin_det.bk = header[17]
            bin_det.b2 = header[18]
            bin_det.tc = header[19]

            self.detector.append(bin_det)

            size = bin_det.nx * bin_det.ny * bin_det.nz * 4
            if fortran.skip(f) != size:
                raise IOError("Invalid USRBIN file")
        f.close()

    # ----------------------------------------------------------------------
    # Read detector data
    # ----------------------------------------------------------------------
    def readData(self, n):
        """Read detector det data structure"""
        f = open(self.file, "rb")
        fortran.skip(f)
        for i in range(n):
            fortran.skip(f)  # Detector Header
            fortran.skip(f)  # Detector data
        fortran.skip(f)  # Detector Header
        data = fortran.read(f)  # Detector data
        f.close()
        return data

    # ----------------------------------------------------------------------
    # Read detector statistical data
    # ----------------------------------------------------------------------
    def readStat(self, n):
        """Read detector n statistical data"""
        if self.statpos < 0:
            return None
        f = open(self.file, "rb")
        f.seek(self.statpos)
        for i in range(n):
            fortran.skip(f)  # Detector Data
        data = fortran.read(f)
        f.close()
        return data

    # ----------------------------------------------------------------------
    def say(self, det=None):
        """print header/detector information"""
        if det is None:
            self.sayHeader()
        else:
            bin = self.detector[det]
            say("Bin    : ", bin.nb)
            say("Title  : ", bin.name)
            say("Type   : ", bin.type)
            say("Score  : ", bin.score)
            say("X      : [", bin.xlow, "-", bin.xhigh, "] x", bin.nx, "dx=", bin.dx)
            say("Y      : [", bin.ylow, "-", bin.yhigh, "] x", bin.ny, "dy=", bin.dy)
            say("Z      : [", bin.zlow, "-", bin.zhigh, "] x", bin.nz, "dz=", bin.dz)
            say("L      : ", bin.lntzer)
            say("bk     : ", bin.bk)
            say("b2     : ", bin.b2)
            say("tc     : ", bin.tc)


# ===============================================================================
# MGDRAW output
# ===============================================================================
class Mgdraw:
    def __init__(self, filename=None):
        """Initialize a MGDRAW structure"""
        self.reset()
        if filename is None:
            return
        self.open(filename)

    # ----------------------------------------------------------------------
    def reset(self):
        """Reset information"""
        self.file = ""
        self.hnd = None
        self.nevent = 0
        self.data = None

    # ----------------------------------------------------------------------
    # Open file and return handle
    # ----------------------------------------------------------------------
    def open(self, filename):
        """Read header information, and return the file handle"""
        self.reset()
        self.file = filename
        try:
            self.hnd = open(self.file, "rb")
        except IOError:
            self.hnd = None
        return self.hnd

    # ----------------------------------------------------------------------
    def close(self):
        self.hnd.close()

    # ----------------------------------------------------------------------
    # Read or skip next event from mgread structure
    # ----------------------------------------------------------------------
    def readEvent(self, e_type=None):
        # Read header
        data = fortran.read(self.hnd)
        if data is None:
            return None
        if len(data) == 20:
            ndum, mdum, jdum, edum, wdum \
                = struct.unpack("=iiiff", data)
        else:
            raise IOError("Invalid MGREAD file")

        self.nevent += 1

        if ndum > 0:
            if e_type is None or e_type == 0:
                self.readTracking(ndum, mdum, jdum, edum, wdum)
            else:
                fortran.skip(self.hnd)
            return 0
        elif ndum == 0:
            if e_type is None or e_type == 1:
                self.readEnergy(mdum, jdum, edum, wdum)
            else:
                fortran.skip(self.hnd)
            return 1
        else:
            if e_type is None or e_type == 2:
                self.readSource(-ndum, mdum, jdum, edum, wdum)
            else:
                fortran.skip(self.hnd)
            return 2

    # ----------------------------------------------------------------------
    def readTracking(self, ntrack, mtrack, jtrack, etrack, wtrack):
        self.ntrack = ntrack
        self.mtrack = mtrack
        self.jtrack = jtrack
        self.etrack = etrack
        self.wtrack = wtrack
        data = fortran.read(self.hnd)
        if data is None:
            raise IOError("Invalid track event")
        fmt = "=%df" % (3 * (ntrack + 1) + mtrack + 1)
        self.data = struct.unpack(fmt, data)
        return ntrack

    # ----------------------------------------------------------------------
    def readEnergy(self, icode, jtrack, etrack, wtrack):
        self.icode = icode
        self.jtrack = jtrack
        self.etrack = etrack
        self.wtrack = wtrack
        data = fortran.read(self.hnd)
        if data is None:
            raise IOError("Invalid energy deposition event")
        self.data = struct.unpack("=4f", data)
        return icode

    # ----------------------------------------------------------------------
    def readSource(self, ncase, npflka, nstmax, tkesum, weipri):
        self.ncase = ncase
        self.npflka = npflka
        self.nstmax = nstmax
        self.tkesum = tkesum
        self.weipri = weipri

        data = fortran.read(self.hnd)
        if data is None:
            raise IOError("Invalid source event")
        fmt = "=" + ("i8f" * npflka)
        self.data = struct.unpack(fmt, data)
        return ncase

# ===============================================================================
if __name__ == "__main__":
    import sys

    say("=" * 80)
    usr = Usrbdx(sys.argv[1])
    usr.say()
    for i, _ in enumerate(usr.detector):
        say("-" * 50)
        usr.say(i)
        data = unpackArray(usr.readData(i))
        stat = unpackArray(usr.readStat(i))
