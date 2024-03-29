import sys
import argparse

from pymchelper.input_output import fromfile


def main(args=None):
    """
    Reading two files, one generated by Fluka and one generated by SHIELD-HIT12A
    :param args:
    :return:
    """
    if args is None:
        args = sys.argv[1:]

    # parsing command line options
    parser = argparse.ArgumentParser(args)
    parser.add_argument("--fluka", help='binary file generated with Fluka', type=str, required=True)
    parser.add_argument("--shield", help='binary file generated with SHIELD-HIT12A', type=str, required=True)
    parsed_args = parser.parse_args(args)

    # paths to binary files
    fluka_file_path = parsed_args.fluka
    sh12a_file_path = parsed_args.shield

    # creating empty Detector object and filling it with data read from Fluka file
    fluka_data = fromfile(fluka_file_path)

    # same as above but reading from SHIELD-HIT12A file
    sh12a_data = fromfile(sh12a_file_path)

    # printing some output on the screen
    print("Fluka bins in X: {:d}, Y: {:d}, Z: {:d}".format(fluka_data.x.n, fluka_data.y.n, fluka_data.z.n))
    print("First bin of fluka data", fluka_data.pages[0].data[0, 0, 0, 0, 0])

    print("SHIELD-HIT12A bins in X: {:d}, Y: {:d}, Z: {:d}".format(sh12a_data.x.n, sh12a_data.y.n, sh12a_data.z.n))
    print("First bin of SHIELD-HIT12A data", sh12a_data.pages[0].data[0, 0, 0, 0, 0])

    # comparing file contents
    print("Difference Fluka - SHIELD-HIT12A", (sh12a_data.data_raw - fluka_data.data_raw)[0:5], "...")


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
