import setuptools
from pkg_resources import parse_version


def pip_command_output(pip_args):
    """
    Get output (as a string) from pip command
    :param pip_args: list o pip switches to pass
    :return: string with results
    """
    import sys
    import pip
    from io import StringIO
    # as pip will write to stdout we use some nasty hacks
    # to substitute system stdout with our own
    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()
    pip.main(pip_args)
    output = mystdout.getvalue()
    mystdout.truncate(0)
    sys.stdout = old_stdout
    return output


def setup_versioneer():
    """
    Generate (temporarily) versioneer.py file in project root directory
    :return:
    """
    try:
        # assume versioneer.py was generated using "versioneer install" command
        import versioneer
        versioneer.get_version()
    except ImportError:
        # it looks versioneer.py is missing
        # lets assume that versioneer package is installed
        # and versioneer binary is present in $PATH
        import subprocess
        try:
            # call versioneer install to generate versioneer.py
            subprocess.check_output(["versioneer", "install"])
        except OSError:
            # it looks versioneer is missing from $PATH
            # probably versioneer is installed in some user directory

            # query pip for list of files in versioneer package
            # line below is equivalen to putting result of
            #  "pip show -f versioneer" command to string output
            output = pip_command_output(["show", "-f", "versioneer"])

            # now we parse the results
            import os
            # find absolute path where *versioneer package* was installed
            # and store it in main_path
            main_path = [x[len("Location: "):] for x in output.splitlines()
                         if x.startswith("Location")][0]
            # find path relative to main_path where
            # *versioneer binary* was installed
            bin_path = [x[len("  "):] for x in output.splitlines()
                        if x.endswith(os.path.sep + "versioneer")][0]

            # exe_path is absolute path to *versioneer binary*
            exe_path = os.path.join(main_path, bin_path)
            # call versioneer install to generate versioneer.py
            # line below is equivalent to running in terminal
            # "python versioneer install"
            subprocess.check_output(["python", exe_path, "install"])


def clean_cache():
    """
    Python won't realise that new module has appeared in the runtime
    We need to clean the cache of module finders. Hacking again
    :return:
    """
    import importlib
    try:  # Python ver < 3.3
        vermod = importlib.import_module("versioneer")
        globals()["versioneer"] = vermod
    except ImportError:
        importlib.invalidate_caches()


def get_version():
    """
    Get project version (using versioneer)
    :return: string containing version
    """
    setup_versioneer()
    clean_cache()
    import versioneer
    version = versioneer.get_version()
    parsed_version = parse_version(version)
    if '*@' in parsed_version[1]:
        import time
        version += str(int(time.time()))
    return version


def get_cmdclass():
    """
    Get setuptools command class
    :return:
    """
    setup_versioneer()
    clean_cache()
    import versioneer
    return versioneer.get_cmdclass()


with open('README.rst') as readme_file:
    readme = readme_file.read()


setuptools.setup(
    name='pymchelper',
    version=get_version(),
    packages=setuptools.find_packages(where='.', exclude=("*.tests", "*.tests.*", "tests.*", "tests")),
    url='https://github.com/DataMedSci/pymchelper',
    license='MIT',
    author='Leszek Grzanka',
    author_email='grzanka@agh.edu.pl',
    description='Python toolkit for SHIELD-HIT12A and Fluka',
    long_description=readme + '\n',
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    entry_points={
        'console_scripts': [
            'convertmc=' + \
            'pymchelper.run:main',
            'pld2sobp=pymchelper.utils.pld2sobp:main',
        ],
    },
    install_requires=[
        'enum34',
        'numpy'
    ],
    cmdclass=get_cmdclass()
)
