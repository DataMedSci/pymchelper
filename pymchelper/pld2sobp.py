#!/usr/bin/env python
""" Reads PLD file in IBA format and convert to sobp.dat 
    which is readbale by FLUKA with source_sampler.f and SHIELD-HIT12A.

    Niels Bassler 23.2.2016
    <bassler@phys.au.dk>

   TODO: Translate energy to spotsize.
E[MeV]    sigmaY_GCS [mm]    sigmaX_GCS [mm]
70    6,476    6,358
80    5,944    5,991
90    5,437    5,352
100    5,081    5,044
110    4,820    4,828
120    4,677    4,677
130    4,401    4,431
140    4,207    4,104
150    3,977    3,956
160    3,758    3,687
170    3,609    3,477
180    3,352    3,288
190    3,131    3,034
200    2,886    2,803
210    2,713    2,645
220    2,529    2,461
225    2,522    2,452


"""




import os
import sys
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-f", "--flip", dest="flip",
                  action="store_true", default=False,
                  help="Flip XY axis.")
(options, args) = parser.parse_args()


def dEdx(energy):
    ''' PSTAR stopping power for interval 10 - 250 MeV '''
    ''' Energy is in MeV '''
    ''' Stopping power is in MeV cm2/g            '''

    if (energy > 250.0) or (energy < 10.0):
        print "dEdx error: ",energy, "MeV is out of bounds."
        quit

    a0 = 265.78
    a1 = -0.828879
    a2 = 0.647173

    return a0*pow(energy,a1)+a2


class Layer(object):

    def __init__(self,spotsize,energy,meterset,elsum,elements):
        self.spotsize = float(spotsize)
        self.energy = float(energy)
        self.meterset = float(meterset) # MU sum of this + all previous layers
        self.elsum = float(elsum) # sum of elements in this layer
        #self.repaints = int(repaints) # number of repaints
        self.elements = elements # number of elements
        self.spots = int(len(elements)/2)

        self.x = [0.0] * self.spots
        self.y = [0.0] * self.spots
        self.w = [0.0] * self.spots  # MU weight
        self.rf = [0.0] * self.spots # fluence weight

        j = 0

        for i in range(len(elements)):
            token =  elements[i].split(",")
            if token[3] != "0.0":
                self.x[j] = float(token[1].strip())
                self.y[j] = float(token[2].strip())
                self.w[j] = float(token[3].strip())
                self.rf[j] = self.w[j] / dEdx(self.energy)

                j += 1
                #rint token



class PLDRead(object):
    ''' This file reads PLD riles'''
    FileIsRead = False

    def __init__(self,filename):
        """ Read the rst file."""
        #print 'initialized with filename',  filename

        if os.path.isfile(filename) is False:
            raise IOError,  "Could not find file " + filename
        else:
            pldfile = open(filename, 'r')
            pldlines = pldfile.readlines()
            pldfile.close()
            pldlen=len(pldlines)
            print "read",pldlen,"lines of data."
            i = 0
            layer_cnt = 0
            self.layer = []

            # parse first line
            token = pldlines[0].split(",")
            #print token
            self.beam = token[0].strip()
            self.patient_iD = token[1].strip()
            self.patient_name = token[2].strip()
            self.patient_initals = token[3].strip()
            self.patient_firstname = token[4].strip()
            self.plan_label = token[5].strip()
            self.beam_name  = token[6].strip()
            self.mu = float(token[7].strip())
            self.csetweight = float(token[8].strip())
            self.layers = int(token[9].strip())
            i += 1
            #print "done"

            while i < pldlen:
                line = pldlines[i]
                #rint line
                if "Layer" in line:
                    header = line
                    token = header.split(",")
                    print token[0],token[1],token[2],token[3],token[4].strip()
                    # extract the subsequent lines with elements
                    el_first = i+1
                    el_last = el_first + int(token[4])

                    elements = pldlines[el_first:el_last]

                    self.layer.append(Layer(token[1].strip(),
                                            token[2].strip(),
                                            token[3].strip(),
                                            token[4].strip(),
#                                            token[5].strip(),
                                            elements))
                i += 1

#
#
#

fn = args[0]

if os.path.isfile(fn) == False:
    print "No such file ",fn
    quit

a = PLDRead(fn)
fout = open("sobp.dat",'w')
for i in range(a.layers):
    l = a.layer[i]
    for j in range(l.spots):

        if options.flip == False:        
            fout.writelines("%-10.6f%-10.2f%-10.2f%-10.2f%-10.4e\n" % (l.energy/1000.0, l.x[j]/10.0, l.y[j]/10.0, (l.spotsize/10.0)*2.355, l.rf[j]*a.mu/a.csetweight))
        else:
            fout.writelines("%-10.6f%-10.2f%-10.2f%-10.2f%-10.4e\n" % (l.energy/1000.0, l.y[j]/10.0, l.x[j]/10.0, (l.spotsize/10.0)*2.355, l.rf[j]*a.mu/a.csetweight))
fout.close()


if options.flip:
    print "Output file was XY flipped."
    
