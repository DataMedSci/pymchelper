import os
import setuptools
import sys

from pymchelper.version import git_version


def write_version_py(filename=os.path.join('pymchelper', 'VERSION')):
    cnt = """%(version)s
"""

    GIT_REVISION = git_version()
    a = open(filename, 'w')
    try:
        a.write(cnt % {'version': GIT_REVISION})
    finally:
        a.close()


write_version_py()

with open('README.rst') as readme_file:
    readme = readme_file.read()

install_requires = []

# here is table with corresponding numpy versions, and supported python and OS versions
# it is based on inspection of https://pypi.org/project/numpy/
# |---------------------------------------------------|
# | numpy version | python versions |    OS support   |
# |---------------------------------------------------|
# |      1.20     |    3.7 - 3.9    | linux, mac, win |
# |      1.19     |    3.6 - 3.8    | linux, mac, win |
# |      1.18     |    3.5 - 3.8    | linux, mac, win |
# |      1.17     |    3.5 - 3.7    | linux, mac, win |
# |      1.16     | 2.7,  3.5 - 3.7 | linux, mac, win |
# |      1.15     | 2.7,  3.4 - 3.7 | linux, mac, win |
# |      1.14     | 2.7,  3.4 - 3.6 | linux, mac, win |
# |      1.13     | 2.7,  3.4 - 3.6 | linux, mac, win |
# |      1.12     | 2.7,  3.4 - 3.6 | linux, mac, win |
# |      1.11     | 2.7,  3.4 - 3.5 | linux, mac, win |
# |      1.10     | 2.7,  3.3 - 3.5 |      linux      |
# |       1.9     | 2.7,  3.3 - 3.5 |      linux      |
# |---------------------------------------------------|
setup_requires = []
if sys.version_info[0] == 3 and sys.version_info[1] == 9:  # python 3.9
    install_requires += ["numpy>=1.20"]
elif sys.version_info[0] == 3 and sys.version_info[1] == 8:  # python 3.8
    install_requires += ["numpy>=1.18"]
elif sys.version_info[0] == 3 and sys.version_info[1] == 7:  # python 3.7
    install_requires += ["numpy>=1.15"]
elif sys.version_info[0] == 3 and sys.version_info[1] == 6:  # python 3.6
    install_requires += ["numpy>=1.12,<1.20"]
elif sys.version_info[0] == 3 and sys.version_info[1] == 5:  # python 3.5
    install_requires += ["numpy>=1.11,<1.19"]
elif (sys.version_info[0] == 3 and sys.version_info[1] < 5) or (sys.version_info[0] == 2):  # python 3.4 and 2.7
    install_requires += ["numpy>=1.11,<1.16"]
    install_requires += ["enum34"]
else:
    install_requires += ["numpy"]


setuptools.setup(
    name='pymchelper',
    version=git_version(),
    packages=setuptools.find_packages(where='.', exclude=("*.tests", "*.tests.*", "tests.*", "tests", "examples")),
    url='https://github.com/DataMedSci/pymchelper',
    license='MIT',
    author='Leszek Grzanka',
    author_email='leszek.grzanka@gmail.com',
    description='Python toolkit for SHIELD-HIT12A and FLUKA',
    long_description=readme + '\n',
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 5 - Production/Stable',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Scientific/Engineering :: Physics',

        # OS and env
        'Environment :: Console',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Microsoft :: Windows',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9'
    ],
    entry_points={
        'console_scripts': [
            'convertmc=pymchelper.run:main',
            'pld2sobp=pymchelper.utils.pld2sobp:main',
            'mcscripter=pymchelper.utils.mcscripter:main',
        ],
    },
    package_data={'pymchelper': ['flair/db/*', 'VERSION']},
    install_requires=install_requires,
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.3.*',
)
