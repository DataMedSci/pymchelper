# find specification of the pytripgui module
import importlib
import os

# Python2 lacks a FileNotFoundError exception, we use then IOError
try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError

# get location of __init__.py file (the one you see now) in the filesystem
spec = importlib.util.find_spec('pymchelper')
init_location = spec.origin

# VERSION should sit next to __init__.py in the directory structure
version_file = os.path.join(os.path.dirname(init_location), 'VERSION')

try:
    # read first line of the file (removing newline character)
    with open(version_file, 'r') as f:
        __version__ = f.readline().strip()
except FileNotFoundError:
    # backup solution - read the version from git
    from pymchelper.version import git_version
    __version__ = git_version()
