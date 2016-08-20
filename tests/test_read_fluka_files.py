import os
import unittest
import logging

# from pymchelper.flair.Data import Usrbin, unpackArray, Usrbdx, Resnuclei, Usrxxx
import pymchelper.flair.Input as Input

logger = logging.getLogger(__name__)


class TestDefaultConverter(unittest.TestCase):
    main_dir = os.path.join("tests", "res", "fluka")
    generated_dir = os.path.join(main_dir, "generated")

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

    def check_directory(self, dir_path):
        for filename in os.listdir(self.main_dir):
            rel_path = os.path.join(self.main_dir, filename)
            if rel_path.endswith(".inp"):
                logger.info("opening " + rel_path)
                input = Input.Input()
                input.read(rel_path)

                logger.info("checking if START setting is correct ")
                self.assertGreater(int(input.cards["START"][0].whats()[1]), 100.0)

                logger.info("checking if BEAM setting is correct ")
                self.assertEqual(input.cards["BEAM"][0].sdum(), 'PROTON')

                logger.info("checking if more than one USRBIN present")
                self.assertGreater(len(input.cards["USRBIN"]), 1)

    def test_load_input(self):
        self.check_directory(self.main_dir)
        self.check_directory(self.generated_dir)


if __name__ == '__main__':
    unittest.main()
