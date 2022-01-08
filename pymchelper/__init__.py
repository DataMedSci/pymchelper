import importlib
import importlib.util
import os


__version__ = 'unknown'

# versioning of the package is based on __version__ variable, declared here in __init__.py file
# __version__ can be either calculated based on pymchelper/VERSION file, storing version number
# or calculated directly from git repository (in case we work with cloned repo)

# we start by finding absolute path to the directory where pymchelper is installed
# we cannot rely on relative paths as binary files which need version number may be located in different
# directory than the pymchelper module

# get location of __init__.py file (the one you see now) in the filesystem
module_name = 'pymchelper'
spec = importlib.util.find_spec(module_name)
init_location = spec.origin

# VERSION should sit next to __init__.py in the directory structure
version_file = os.path.join(os.path.dirname(init_location), 'VERSION')

# let us try reading the VERSION file,
try:
    # it may be that executable (zipfile with pyz extension) is produced which contains all pymchelper
    # modules files packed together with __main__ script. In that case we cannot simply open file,
    # but we need to reach into the contents of zip file:
    possible_zipfile_path = os.path.normpath(os.path.join(init_location, '..', '..'))
    import zipfile
    if zipfile.is_zipfile(possible_zipfile_path):  # reach into zip file
        with zipfile.ZipFile(possible_zipfile_path, 'r') as zipfile:  # read file from inside ZIP archive
            # read first line of the file (removing newline character)
            vf = os.path.join(module_name, 'VERSION')
            with zipfile.open(vf, 'r') as f:
                __version__ = f.readline().strip().decode('ascii')
    # it looks that pymchelper was installed via pip and unpacked into some site-directory folder in the file system
    # in such case we simply read the VERSION file
    else:
        # read first line of the file (removing newline character)
        with open(version_file, 'r') as f:
            __version__ = f.readline().strip()

# in case above methods do not work, let us assume we are working with GIT repository
except FileNotFoundError:
    # backup solution - read the version from git
    from pymchelper.version import git_version
    __version__ = git_version()
