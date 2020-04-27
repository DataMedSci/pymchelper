# find specification of the pytripgui module
import os
import sys

# Python2 lacks a FileNotFoundError exception, we use then IOError
try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError

PY3 = sys.version_info > (3, 0)
# get location of __init__.py file (the one you see now) in the filesystem
module_name = 'pymchelper'
if not PY3:  # Python 2
    import imp
    init_location = imp.find_module(module_name)[1]
else:  # Python >= 3.4
    import importlib
    import importlib.util
    spec = importlib.util.find_spec(module_name)
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
