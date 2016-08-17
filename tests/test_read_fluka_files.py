import os
import unittest
import logging

from pymchelper.flair.Data import Usrbin, unpackArray, Usrbdx, Resnuclei, Usrxxx

logger = logging.getLogger(__name__)


class TestDefaultConverter(unittest.TestCase):
    main_dir = os.path.join("tests", "res", "fluka")

    def read_data(self, usr):
        for i in range(len(usr.detector)):
            logger.debug("-" * 20 + (" Detector number %i " % i) + "-" * 20)
            usr.say(i)  # details for each detector
        data = usr.readData(0)
        fdata = unpackArray(data)
        print(fdata.shape)

    def check(self, rel_path):
        try:
            usr = Usrbin(rel_path)
            usr.sayHeader()  # file,title,time,weight,ncase,nbatch
            usr.say()  # file,title,time,weight,ncase,nbatch
            self.read_data(usr)
            print("!!! File ", rel_path, " is Usrbin")
            return
        except Exception as e:
            print(e)
            print("File ", rel_path, " is not Usrbin")

        try:
            usr = Usrbdx(rel_path)
            usr.sayHeader()  # file,title,time,weight,ncase,nbatch
            usr.say()  # file,title,time,weight,ncase,nbatch
            self.read_data(usr)
            print("!!! File ", rel_path, " is Usrbdx")
            return
        except Exception as e:
            print(e)
            print("File ", rel_path, " is not Usrbdx")

        try:
            usr = Resnuclei(rel_path)
            usr.sayHeader()  # file,title,time,weight,ncase,nbatch
            usr.say()  # file,title,time,weight,ncase,nbatch
            self.read_data(usr)
            print("!!! File ", rel_path, " is Resnuclei")
            return
        except Exception as e:
            print(e)
            print("File ", rel_path, " is not Resnuclei")

        try:
            usr = Usrxxx(rel_path)
            usr.sayHeader()  # file,title,time,weight,ncase,nbatch
            self.read_data(usr)
            print("!!! File ", rel_path, " is Usrxxx")
            return
        except Exception as e:
            print(e)
            print("File ", rel_path, " is not Usrxxx")
        print("File ", rel_path, " cannot be opened")
        return

    def test_load_files(self):
        # loop over all .bdo files in all subdirectories
        for filename in os.listdir(self.main_dir):
            rel_path = os.path.join(self.main_dir, filename)
            print("\n\nopening", rel_path)
            self.check(rel_path)


if __name__ == '__main__':
    unittest.main()
