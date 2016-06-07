import argparse
import os
import subprocess

import numpy as np


def process_output_windows(verbose=False):
    """
    Call "tasklist" Windows system command and
    give back its output in form of numpy array
    :param verbose:
    :return:
    """
    out_bytes = subprocess.check_output(["tasklist", "/FO", "CSV"])
    out_text = out_bytes.decode('cp1250')
    tmp_list = []
    for line in out_text.split("\r\n")[3:]:
        items = line.split(",")
        if len(items) > 4:
            command = items[0]
            pid = int(items[1][1:-1])
            cpu = float(items[1][1:-1])
            tmp_list.append((pid, cpu, command))
            if verbose:
                print("pid", pid, "cpu", cpu, command)
    dtype = [('pid', int), ('cpu', float), ('name', 'S1000')]
    tmp_array = np.array(tmp_list, dtype=dtype)
    return tmp_array


def process_output_linux(verbose=False):
    """
    Call "ps aux" Linux system command and
    give back its output in form of numpy array
    :param verbose:
    :return:
    """
    out_bytes = subprocess.check_output(["ps", "aux"])
    out_text = out_bytes.decode('ascii')
    tmp_list = []
    for line in out_text.split("\n")[1:]:
        items = line.split()
        if len(items) > 10:
            command = " ".join(items[10:])
            pid = int(items[1])
            cpu = float(items[2])
            tmp_list.append((pid, cpu, command))
            if verbose:
                print("pid", pid, "cpu", cpu, command)
    dtype = [('pid', int), ('cpu', float), ('name', 'S1000')]
    tmp_array = np.array(tmp_list, dtype=dtype)
    return tmp_array


def most_cpu_pid(verbose=False):
    """
    Get pid of most-cpu-intensive process by calling psaux_output
    method and analyse its results
    :param verbose:
    :return:
    """
    if os.name in ['posix']:
        outp = process_output_linux(verbose)
    else:
        outp = process_output_windows(verbose)
    x = np.sort(outp, kind="mergesort", order="cpu")
    most_cpu_item = x[-1]
    pid = most_cpu_item["pid"]
    if verbose:
        print("=" * 100)
        print("Most CPU consuming item",
              pid,
              most_cpu_item["cpu"],
              most_cpu_item["name"])
    return pid


def check(verbose=False):
    """
    Check if PID of most-cpu-intensive process is prime number
    :param verbose:
    :return:
    """
    pid = most_cpu_pid()
    d = 2
    prime = True
    while d <= int(pid ** 0.5):
        if pid % d == 0:
            prime = False
            print(d)
            break
        d += 1
    return prime


def main():
    """
    Main function, called from CLI script
    :return:
    """
    import pymchelper
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose',
                        action='store_true',
                        help='be verbose')
    parser.add_argument('--version',
                        action='version',
                        version=pymchelper.__version__)
    args = parser.parse_args()

    isprime = check(verbose=args.verbose)

    if isprime:
        print("Its prime")
    else:
        print("Its not prime")


if __name__ == '__main__':
    main()
