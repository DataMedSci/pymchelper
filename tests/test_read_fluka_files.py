import os
import unittest
import logging

# from pymchelper.flair.Data import Usrbin, unpackArray, Usrbdx, Resnuclei, Usrxxx
import pymchelper.flair.Input as Input

logger = logging.getLogger(__name__)


class TestDefaultConverter(unittest.TestCase):
    main_dir = os.path.join("tests", "res", "fluka")

    # def read_data(self, usr):
    #     for i in range(len(usr.detector)):
    #         logger.debug("-" * 20 + (" Detector number %i " % i) + "-" * 20)
    #         usr.say(i)  # details for each detector
    #     data = usr.readData(0)
    #     fdata = unpackArray(data)
    #     print(len(fdata), fdata[0:10])

    # def check(self, rel_path):
    #     try:
    #         usr = Usrbin(rel_path)
    #         usr.sayHeader()  # file,title,time,weight,ncase,nbatch
    #         usr.say()  # file,title,time,weight,ncase,nbatch
    #         self.read_data(usr)
    #         print("!!! File ", rel_path, " is Usrbin")
    #         return
    #     except Exception as e:
    #         print(e)
    #         print("File ", rel_path, " is not Usrbin")
    #
    #     try:
    #         usr = Usrbdx(rel_path)
    #         usr.sayHeader()  # file,title,time,weight,ncase,nbatch
    #         usr.say()  # file,title,time,weight,ncase,nbatch
    #         self.read_data(usr)
    #         print("!!! File ", rel_path, " is Usrbdx")
    #         return
    #     except Exception as e:
    #         print(e)
    #         print("File ", rel_path, " is not Usrbdx")
    #
    #     try:
    #         usr = Resnuclei(rel_path)
    #         usr.sayHeader()  # file,title,time,weight,ncase,nbatch
    #         usr.say()  # file,title,time,weight,ncase,nbatch
    #         self.read_data(usr)
    #         print("!!! File ", rel_path, " is Resnuclei")
    #         return
    #     except Exception as e:
    #         print(e)
    #         print("File ", rel_path, " is not Resnuclei")
    #
    #     try:
    #         usr = Usrxxx(rel_path)
    #         usr.sayHeader()  # file,title,time,weight,ncase,nbatch
    #         self.read_data(usr)
    #         print("!!! File ", rel_path, " is Usrxxx")
    #         return
    #     except Exception as e:
    #         print(e)
    #         print("File ", rel_path, " is not Usrxxx")
    #     print("File ", rel_path, " cannot be opened")
    #     return

    # def test_load_files(self):
    #     # loop over all .bdo files in all subdirectories
    #     for filename in os.listdir(self.main_dir):
    #         rel_path = os.path.join(self.main_dir, filename)
    #         print("\n\nopening", rel_path)
    #         self.check(rel_path)

    def test_load_input(self):
        Input.init()

        # input useful functions:
        #  - read/write : read/write an input file
        #  - clone
        # - checkFormat(card) FORMAT_FREE / FORMAT_SINGLE
        # - addCard(card)
        # - delCard(card)
        # - delTag(tag) - delete all cards with specific tag
        # - delGeometryCards
        # - replaceCard(position, card)
        # - convert2Names - Convert input to names and check for obsolete and/or non-valid cards
        # - validate - ??
        # - checkNumbering - ??
        # - minimumInput
        # - renumber
        #
        # Card useful functions:
        # - __init__(self, tag, what=None, comment="", extra="")
        # - clone
        # - appendWhats(self, what, pos=None)
        # - appendComment(self, comment):
        # - validate(self, case=None):
        # - convert(self, tonames=True)
        # - whats(self), nwhats()
        # - sdum
        # - extra
        # - comment
        # - isGeo
        # - type
        # - tag
        # - what(self, n)
        # - setComment(self, comment="")
        # - setWhats(self, whats)
        # - setSdum(self, s)
        # - setExtra(self, e)
        # - setWhat(self, w, v)
        # - units(self, absolute=True) units used by card
        # - commentStr(self)
        # - def toStr(self, fmt=None)
        # - addZone(self, zone)

        #

        for filename in os.listdir(self.main_dir):
            rel_path = os.path.join(self.main_dir, filename)
            if rel_path.endswith(".inp"):
                logger.info("opening " + rel_path)
                input = Input.Input()
                input.read(rel_path)
                input.convert2Names()
                try:
                    rndcard = input.cards["RANDOMIZ"][0]
                    rndcard.setWhat(2, 5723)
                except:
                    logger.error("No RANDOMIZe card found")
                input.write(rel_path[:-3] + "new")
                self.assertTrue(os.path.exists(rel_path[:-3] + "new"))

if __name__ == '__main__':
    unittest.main()
