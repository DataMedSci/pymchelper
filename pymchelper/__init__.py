# Python2 lacks a FileNotFoundError exception, we use then IOError
try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError

try:
    with open('VERSION', 'r') as f:
        __version__ = f.readline(1)
except FileNotFoundError:
    from pymchelper.version import git_version
    __version__ = git_version()
