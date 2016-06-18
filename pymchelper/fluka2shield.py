#!/usr/bin/env python
#
# Written by Niels Bassler <bassler@phys.au.dk>
# 2015 
# 


import os
import sys
import math

# split into geo.dat, beam.dat, mat.dat, proj.dat

class Body:
    def __init__(self):
        self.code = ""
        self.name = ""
        self.number = 0
        self.arg = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0] #max 9 arguments

class Region:
    def __init__(self):
        self.name = ""
        self.number = 0
        self.naz = 0
        self.expr = []
        
class Material:
    def __init__(self):
        self.number = 0
        self._regname = ""
        self.name = ""

class Scorer:
    def __init__(self):
        self.number = 0.0
        self.code = 0.0
        self.detector = ""
        self.forid = 0 #logical output unit number
        self.d1min = ""
        self.d2min = ""
        self.d3min = ""
        self.d1max = ""
        self.d2max = ""
        self.d3max = ""
        self.d1bin = 0.0
        self.d2bin = 0.0
        self.d3bin = 0.0

class MCObject:
    """Class holding all relevant information from """
    """a FLUKA input file."""

    def __init__(self):
        self.data = []
        self.materials = []
        self.scorers = []
        self._uid = 1 # first material
        self.mlist = []
        
        pdglist = "4-HELIUM","3-HELIUM","TRITON","DEUTERON","HEAVYION", \
                  "OPTIPHOT","RAY","PROTON","APROTON","ELECTRON","POSITRON", \
                  "NEUTRIE","ANEUTRIE","PHOTON","NEUTRON","ANEUTRON","MUON+",\
                  "MUON-","KAONLONG","PION+","PION-","KAON+","KAON-","LAMBDA",\
                  "ALAMBDA","KAONSHRT","SIGMA-","SIGMA+","SIGMAZER","PIZERO",\
                  "KAONZERO","AKAONZER","Reserved","NEUTRIM","ANEUTRIM","Blank",\
                  "Reserved","ASIGMA-","ASIGMAZE","ASIGMA+","XSIZERO","AXSIZERO",\
                  "XSI-","AXSI+","OMEGA-","AOMEGA+","Reserved","TAU+","TAU-",\
                  "NEUTRIT","ANEUTRIT","D+","D-","D0","D0BAR","DS+","DS-",\
                  "LAMBDAC+","XSIC+","XSIC0","XSIPC+","XSIPC0","OMEGAC0",\
                  "ALAMBDC-","AXSIC-","AXSIC0","AXSIPC-","AXSIPC0","AOMEGAC0"
        fids = range(-6,65)
        self.fdict = dict(zip(pdglist,fids)) # lookup table

        # make table which links FLUKA id with SH12A JPART
        sids = range(-1,26)
        fff = [201,8,1,14,13,23,9,2,16,15,24,12,7,3,4,11,10,5,6,27,28,-3,-4,-5,-6,-2]
        self.fid_jpart=zip(fff,sids) # return tuple, [0] holds fid, [1] holds JPART

        self.amu = 931.494061
        
        # starting at id = 1, neutron, masses in MeV/c2
        smass = [939.565,# neutron
                 938.272,# proton
                 139.570,# pi-
                 139.570,# pi+
                 134.977,# pi0
                 939.565,# neutron
                 938.272,# proton
                 493.677,# K-
                 493.677,# K+
                 497.614,# K0
                 497.614,# K-long
                   0.000,# photon
                 0.51100,# e-
                 0.51100,# e+
                 105.658,# mu-
                 105.658,# mu+
                 0.0000022,# ve
                 0.0000022,# anti-ve
                 0.00017,# vmu
                 0.00017,# anti-vmu
                 2.01410 * self.amu,# deuteron
                 3.01604 * self.amu,# triton
                 3.01603 * self.amu,# He-3
                 4.00260 * self.amu # He-4
                 ]

        self.shmass = zip(range(1,25),smass)
        
        
    def smass(self,jpart,A=0):
        """ Returns mass from JPART """
        if jpart == 25: # heavy ion case
            return A*self.amu

        # scan for mass
        for jpart1,mass in self.shmass:
            if jpart1 == jpart:
                return mass
            
        # not possible
        print "WARNING, paritcle JPART ",jpart,"does not exist in SH12A."
        return 0.0
        
            
        
    def fid2jpart(self,f):
        """ Returns JPART number from FLUKA id """
        for fid,jpart in self.fid_jpart:
            if int(f) == jpart:
                return jpart
        print "WARNING, fluka paritcle ",f,"does not exist in SH12A."

        

    def load(self,fname):
        fd = open(fname,'r')
        lines = fd.readlines()
        fd.close()

        ilines = iter(lines)
        
        for line in ilines:
            #print ">>>",line,"<<<"
            if line[0] == "*": # skip comments
                continue

            card = self.getcard(line)

#            print "Found card >%s<" %card
            
            if card == "TITLE": # get title
                self.title = next(ilines)
                continue

            
            if card == "BEAM":
                what = self.parsefix(line)
                if what[1] > 0.0:
                    self.beam_momentum = what[1]
                else:
                    self.beam_energy = what[1]

                if what[2] > 0.0:
                    self.beam_momentum_spread_rect = what[2]
                else:
                    self.beam_momentum_spread_fwhm = what[2]

                self.beam_div = what[3]
                self.beam_sx = what[4]                       
                self.beam_sy = what[5]
                self.beam_sflag = what[6]

                #fid = self.pdg2fid(what[7])
                fid = self.fdict[what[7].strip()]
                self.beam = fid
                self.jpart = self.fid2jpart(fid)
                print "self jpart: " ,self.jpart, fid
                self.beam_mass = self.smass(self.jpart)
                continue

            if card == "BEAMPOS":
                what = self.parsefix(line)
                self.beamx = what[1]
                self.beamy = what[2]
                self.beamz = what[3]
                self.dircx = what[4]
                self.dircy = what[5]
                if what[7].strip() == "NEGATIVE":
                    self.dircz = -1
                else:
                    self.dircz = 1
                continue

            if card == "HI-PROPE":
                what = self.parsefix(line)
                self.beamZ = what[1]
                self.beamA = what[2]
            
            if card == "GEOBEGIN":
                print " --- geobegin ---"
                # assume free format
                # get title line
                line = self.getline(ilines, False) # line may be idented, therefor no stripping.
                
                self.geo_ivopt = int(line.split()[0])
                self.geo_idbg = int(line.split()[1])
                self.geo_title = line[20:60]

                line = self.getline(ilines)

                # parse all bodies
                self.bodies = []                
                while card != "END": # get bodies first
                    #print "parsing>%s<" %line
                    self.bodies.append(Body())
                    self.bodies[-1].number = len(self.bodies)
                    self.bodies[-1].code = line.split()[0].strip()
                    self.bodies[-1].name = line.split()[1].strip()
                    if self.bodies[-1].code == "RPP":
                        for i in range(6): # take in 6 arguments
                            self.bodies[-1].arg[i] = line.split()[i+2]
                            self.bodies[-1].argc = 6
                    elif self.bodies[-1].code == "RCC" :
                        for i in range(7): # take in 7 arguments
                            self.bodies[-1].arg[i] = line.split()[i+2]
                            self.bodies[-1].argc = 7
                    elif self.bodies[-1].code == "SPH" :
                        for i in range(4): # take in 4 arguments
                            self.bodies[-1].arg[i] = line.split()[i+2]
                            self.bodies[-1].argc = 4
                    else:
                        print "unknown body",line
                        exit()

                    line = self.getline(ilines)                    
                    card = self.getcard(line)
                print " --- finished reading bodies --- "

                # next get the regions
                print " --- get regions ---"

                line = self.getline(ilines)
                card = self.getcard(line)

                self.regions = []
                while card != "END": # get regions
                    #print "REGparsing>%s<" %line

                    spline = iter(line.split()) # create iterable of current line splitted

                    tstr = spline.next()
                    if tstr[0].isalnum(): # we have a new region if first char is a letter or number
                        self.regions.append(Region())
                        self.regions[-1].number = len(self.regions)
                        self.regions[-1].name = tstr.strip()                        
                        self.regions[-1].naz = int(spline.next())
                        self.regions[-1].mid = -1 # material id placeholder, set to -1 for no assignment.
                    # get and append each region, and hope there are no ()
                    for token in spline:
                        self.regions[-1].expr.append(token)

                    # read next line and loop
                    line = self.getline(ilines)
                    card = self.getcard(line)

                print " --- done REGparsing ---"
                        
            if card == "ASSIGNMA": # get title  ... this card assigned a Region to a MATERIAL.
                #print "parse assignmat", line
                what = self.parsefix(line)

                _matname =  what[1].strip()
                _mid = -1
                
                # now see if material is known, if not, make a new entry in material list.
                if _matname in self.mlist:
                    # look up mid in material data base
                    for mat in self.materials:
                        if mat.name == _matname:
                            _mid = mat.mid
                else:
                    print "Found new material", _matname

                    self.mlist.append(_matname)                    
                    self.materials.append(Material())
                    
                    self.materials[-1].number = len(self.materials)
                    self.materials[-1].name = _matname

                    if self.materials[-1].name == "BLCKHOLE":
                        self.materials[-1].mid = 0
                    elif self.materials[-1].name == "VACUUM":
                        self.materials[-1].mid = 1000
                    else:
                        self.materials[-1].mid = self._uid
                        self._uid += 1
                        print "Material ", self.materials[-1].name, "is now assigned to material id#", \
                        self.materials[-1].mid
                    _mid = self.materials[-1].mid


                # loop over all regions and assign the fitting material id (mid)
                _regname = what[2].strip()
                for region in self.regions:
                    if region.name == _regname:
                        region.mid = _mid
                        print "Assigned material", _matname, "to region", _regname

                _lastreg = what[3].strip()
                if _lastreg != "" : # a range was specified
                    score = False
                    last = False
                    for region in self.regions:
#                    irg = iter(self.regions)
#                    for rg in irg: # for all regions
#                        if rg.name == _regname :  # starting from what[2]
                        if region.name == _regname:
                            score = True

                        if region.name == _lastreg : # until what[3]
                            last = True

                        if score:
                            region.mid = _mid
                            print "Loop assigned material id ", _mid, "to region", region.name
                            if last:
                                score = False
                # assign a unique MATERIAL ID to each unique material

                continue

            if card == "USRBIN":
                
                what = self.parsefix(line,nofloat=True)

                if what[7].strip() != "&": # we got a new card
                    #print "Found an estimator"
                    self.scorers.append(Scorer())
                    self.scorers[-1].number = len(self.scorers)
                    self.scorers[-1].code = int(float(what[1]))
                    self.scorers[-1].detector = what[2].strip()
                    self.scorers[-1].forid = int(float(what[3]))
                    self.scorers[-1].d1max = what[4]
                    self.scorers[-1].d2max = what[5]
                    self.scorers[-1].d3max = what[6]
                    self.scorers[-1].title = what[7]
                    
                else: # we got a continuation card
                    self.scorers[-1].d1min = what[1]
                    self.scorers[-1].d2min = what[2]
                    self.scorers[-1].d3min = what[3]

                     # need to be parsed to get rid of floats which SH12 doesnt like.
                    self.scorers[-1].d1bin = self.ffloat(what[4]) 
                    self.scorers[-1].d2bin = self.ffloat(what[5])
                    self.scorers[-1].d3bin = self.ffloat(what[6])

                    
                continue

            if card == "START":
                what = self.parsefix(line)
                self.start = what[1]
                continue

            if card == "RANDOMIZ":
                what = self.parsefix(line)
                self.rndunit = self.ffloat(what[1],1.0)
                self.seed = self.ffloat(what[2],54217137.0) # default seed number in FLUKA, see manual.
                continue
        print " ------ PARSING COMPLETED ------ "

        # if momentum was defined, we need to translate to energy
        try:
            self.beam_energy = self.p2energy(self.beam_momentum,self.beam_mass)
        except:
            pass
        
            

    def p2energy(self,p,mass):
        p = p * 1000.0 # convert to MeV/c2
        return  math.sqrt( p*p + mass*mass ) - mass

    def write(self,mode="SH12A"):
        if mode=="SH12A":
            self.writesh_beam()
            self.writesh_geo()
            self.writesh_mat()
            self.writesh_det()
        else:
            print "other write modes not implemented."

            
    def writesh_beam(self):
        fd = open("beam.dat","w")
        print "Generate beam.dat ... :"

        s = ""
        s += "*\n"
        s += "* FLUKA2SHIELD autogenerated beam parameter list. \n"
        s += "*\n"
                
        s += self.sform("RNDSEED","Random seed", [int(self.seed)])

        s += self.sform("JPART0","Projectile", [self.jpart])
        
        if self.beam == -2:
            s += self.sform("HIPROJ","A and Z of heavy ion",[int(self.beamZ),int(self.beamA)])
        
        sarg = "%.3f" % self.beam_energy    
        s += self.sform("TMAX0","Incident energy; (MeV/nucl)", [sarg,0.0])

        s += self.sform("NSTAT","Statistics, step of saving", [int(self.start),int(self.start/4.0) ])
                       
        s += self.sform("BEAMPOS","Beam position", [self.beamx,self.beamy,self.beamz])

        ## BEAM SIGMA
        fwhm = 2*math.sqrt(2*math.log(2))
        if self.beam_sx < 0.0:
            bsx =  "%.5f" % (float(-1.0* self.beam_sx)/fwhm)
        else:
            bsx = "%.5f" % (float(-1.0 * self.beam_sx/2.0))

        if self.beam_sy < 0.0:        
            bsy =  "%.5f" % (float(-1.0 * self.beam_sy)/fwhm)
        else:
            bsy = "%.5f" % (float(-1.0 * self.beam_sy/2.0))
        s += self.sform("BEAMSIGMA","Beam size", [bsx,bsy])
                
        ## DIVERGENCE 
        divx = self.beam_div * -1.0
        divy = divx # in fluka no separation between x and y
        focus = 0.0        
        s += self.sform("BEAMDIV","Divergence and focus", [divx,divy,focus])        


        ## BEAMDIR
        # todo: convert direction cosines to ALT/AZ system of SH12A
        s += self.sform("BEAMDIR","", [0,0])

        ## MISCELANEOUS
        s += self.sform("STRAGG","Straggling", [2])
        s += self.sform("MSCAT","Mult. scattering", [2])
        s += self.sform("NUCRE","Nuclear reaction switch", [1])

        print s
        fd.write(s)
        fd.close()
        
    def writesh_geo(self):
        fd = open("geo.dat","w")
        print "Generate geo.dat..."

        s = "%5i" % int(self.geo_ivopt)
        s += "%5i" % int(self.geo_idbg)
        s += "".rjust(10)
        s += self.geo_title.ljust(60)
        s += "\n"
        s += "*---><---><--------><--------><--------><--------><--------><-------->\n"
        # add all bodies:
        for body in self.bodies:
            s += body.code.rjust(5)
            s += "%5i" % body.number
            for ii in range(body.argc):
                if ii == 6:
                    s += "\n"+"".rjust(10)
                s+= body.arg[ii].rjust(10)
            s+="\n"
        s+="  END\n"        
        print s
        fd.write(s)


        # -------- ZONEs ----------
        # comment for zones
        scom_zone = "*.<-><--->..<--->OR<--->OR<--->OR<--->OR<--->OR<--->OR<--->OR<--->OR<--->\n"
        s = ""
        s += scom_zone
        
        # add all zones
        for region in self.regions:
            ii = 1
            s += "  " +"%03i" % region.number
            s += "     "
            for token in region.expr:
                if ii == 9:
                    s += "\n" + "".rjust(10)
                    ii = 0
                ii += 1
                    
                tname = token[1:]

#               print "TOken:", token,tname
                # loop over all bodies, to find matching number
                n = 0
                for body in self.bodies:
                    n +=1
                    if tname == body.name:
                        ntoken = token.replace(tname,str(n))
#                       print "token replaced:", token, "-->", ntoken
                        break
                s += "  " # placeholder for "OR"
                s += ntoken.rjust(5)                
            s += "\n"
        s += scom_zone
        s += "  END\n"
        print s
        fd.write(s)


        # add material assignments to each zone
        scom_mat = "*---><---><---><---><---><---><---><---><---><---><---><---><---><--->\n"
        s = ""
        s += scom_mat
        m = ""
        m += scom_mat
        j = 0
        k = 0
        for i in range(len(self.regions)):
            if j == 14:   # only 14 items per line. If we exceed, add a \n and resume on next line.
                s+= "\n"
                j = 0
            j += 1

            s += "%5i" % (i+1)
            print "current region name", i, self.regions[i].name, self.regions[i].mid            

            if k == 14: # max 14 per line
                m += "\n"
                k = 0
            k += 1
            m += "%5i" % self.regions[i].mid
                    
        s += "\n"
        m += "\n"
        m += scom_mat
        print s
        fd.write(s)
        print m
        fd.write(m)
        
        fd.close()
        
    def writesh_mat(self):
        # so far count on manual inclusion of materials

        s = "*\n"
        s += "* FLUKA2SHIELD autogenerated material list. \n"
        s += "* Add material definitions manually.\n"
        s += "*\n"
        for mat in self.materials:
            if mat.mid != 0 and mat.mid != 1000:
                s += "MEDIUM %i\n" % mat.mid
                s += "ICRU ***\n"
                s += "END\n"

        fd = open("mat.dat","w")
        fd.write(s)
        fd.close()
        
    def writesh_det(self):

        scom_det = "*----0---><----1---><----2---><----3---><----4---><----5---><----6--->\n"
        
        s = ""
        s += "*\n"
        s += "* FLUKA2SHIELD autogenerated detector list. \n"
        s += "*\n"
        s += scom_det

        padf = " "*10 # padding field for SH12A.
        
        _rstart1 = padf
        _rstop1 = padf

        _rstart2 = padf
        _rstop2 = padf

        _rstart3 = padf
        _rstop3 = padf

        
        
        # type, xyz min, xyz max, bins, particles, detect, fname.

        for sc in self.scorers:

            # do the last bit first of the output
            #  particles, detector, filename
            _suffix = str(-1).rjust(10)
            if sc.detector == "ENERGY":
                if sc.title.strip()=="ALANINE":
                    _suffix += "ALANINE".rjust(10)
                else:
                    _suffix += "ENERGY".rjust(10)

                    
            else :
                _suffix += "unknown".rjust(10)
            fname = "fort." + str(abs(sc.forid))
            _suffix += fname.rjust(10)
            _suffix += "\n"


            # now build the beginning

            
            if sc.code == 10: # cartesian symmetry
                s += "MSH       "
            elif sc.code == 11: # cylindrical symmetry                
                s += "CYL       "
            elif sc.code == 12: # zones
                # lookup start zone number
                for region in self.regions:
                    if region.name == sc.d1min.strip():
                        _rstart1 = str(region.number).rjust(10)
                    if region.name == sc.d1max.strip():
                        _rstop1 = str(region.number).rjust(10)
                    if region.name == sc.d2min.strip():
                        _rstart2 = str(region.number).rjust(10)
                    if region.name == sc.d2max.strip():
                        _rstop2 = str(region.number).rjust(10)
                    if region.name == sc.d3min.strip():
                        _rstart3 = str(region.number).rjust(10)
                    if region.name == sc.d3max.strip():
                        _rstop3 = str(region.number).rjust(10)
                        
                if _rstart1 == padf or _rstop1 == padf:
                    print "Warning didn't find proper region scoring in USRBIN set nr. ", sc.number

                if _rstart1 != padf and _rstop1 != padf:
                    if _rstop1.strip() == _rstart1.strip(): # just pretty print, if only one zone, just write the the start zone
                        _rstop1 = padf
                    s += "ZONE".ljust(10)+_rstart1 + _rstop1 + padf + _suffix
                if _rstart2 != padf and _rstop2 != padf:
                    if _rstop2 == _rstart2: # just pretty print, if only one zone, just write the the start zone
                        _rstop2 = padf
                    s += "ZONE".ljust(10)+_rstart2 + _rstop2 + padf + _suffix
                if _rstart3 != padf and _rstop3 != padf:
                    if _rstop3 == _rstart3: # just pretty print, if only one zone, just write the the start zone
                        _rstop3 = padf
                    s += "ZONE".ljust(10)+_rstart3 + _rstop3 + padf + _suffix

                    
                
            else:
                print "Warning, unsupported scorer: ", sc.code


                
            if sc.code == 10 or sc.code == 11:

                s += sc.d1min.rjust(10) + sc.d2min.rjust(10) + sc.d3min.rjust(10)
                s += sc.d1max.rjust(10) + sc.d2max.rjust(10) + sc.d3max.rjust(10) + "\n"

                s += padf
                s += "%10i%10i%10i" % (sc.d1bin,sc.d2bin,sc.d3bin)


                s += _suffix    
            s += scom_det 
                
        fd = open("detect.dat","w")
        fd.write(s)
        fd.close()
        pass

    
    def sform(self,key,comment,args):
        s = key.ljust(16)
        for arg in args:
            s += str(arg).ljust(10)
        
        s += "".ljust(10*(3-len(args))) +  "! "+comment+"\n"
        return s

                
    def ffloat(self,sf,default=0.0):
        """ Converts to float, but if white space, init to default zero """
        try:
            return float(sf)
        except:
            return default

    def getline(self,ilines,strip=True):
        """ Return next valid line to be parsed """

        if strip:
            line = next(ilines).strip()
        else:
            line = next(ilines)

        if line.startswith("#if 0"): # skip following deactivated lines
            while line != "#endif".strip():
                print "skipped",line
                if strip:
                    line = next(ilines).strip()
                else:
                    line = next(ilines)

        while line[0] == "#":
            print "skipped",line
            if strip:
                line = next(ilines).strip()
            else:
                line = next(ilines)
                
        while line[0] == "*":
            print "skipped",line
            if strip:
                line = next(ilines).strip()
            else:
                line = next(ilines)
        return line        
        
                
    def getcard(self,fline):
        """ Get name of this card from line """
        card = fline[0:10].split()
        #print "getcard:",fline, card
        return card[0]
                
                
    def parsefix(self,fline,nofloat=False):
        """ Returns list of arguments for this line """
        """ Return types in list are tried to be casted into float """
        """ and are string if unsuccessfull. """
        what = []

        fline.ljust(80) # pad with spaces in case that our sting is shorter than 80 chars.        

        if nofloat:
            what.append(fline[0:10])
            what.append(fline[10:20])
            what.append(fline[20:30])
            what.append(fline[30:40])
            what.append(fline[40:50])
            what.append(fline[50:60])
            what.append(fline[60:70])
            what.append(fline[70:80])
            return what
        
        what.append(fline[0:10])
        what.append(self.gettoken(fline[10:20]))
        what.append(self.gettoken(fline[20:30]))
        what.append(self.gettoken(fline[30:40]))
        what.append(self.gettoken(fline[40:50]))
        what.append(self.gettoken(fline[50:60]))
        what.append(self.gettoken(fline[60:70]))
        what.append(fline[70:80])
        return what

    def gettoken(self,token):
        """ Try to parse token as float, if it fails, return a stripped string."""
        tstr = token.strip()
        if tstr == "":
            return tstr
        try:
            tflt = float(tstr)
            return tflt
        except:
            return tstr
        
    

# ---------------------------------------------------------------------
        
foo = MCObject()
foo.load(sys.argv[1])
foo.write()

