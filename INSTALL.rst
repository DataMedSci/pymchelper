.. highlight:: shell

Installation guide
==================

If you are familiar with python and pip tool, simply type following command to install the package::

    $ pip install pymchelper

and::

   $ pip install matplotlib
   $ pip install pytrip98

to get the recommended dependencies enabling `image` and `tripcube` converters respectively.

If your are a less advanced user, read the rest of the page.

Installation guide is divided in three phases:

* prerequisites (mainly Python installation)
* main package installation
* recommended dependency installation

There are two groups of users: full-control (administrator) and limited-control (regular ones).
It might sound strange, but if you own a PC with Windows or Linux installed and are the only user of it,
then the full-control (administrator) instruction if for you.

For limited users we assume that they can write files to their home directory, but not necessary elsewhere.
An example of limited users are those who are using computing cluster. Typically the access to cluster
is given to many users and none of them has administrator rights.

This instruction is mainly targeted ar full-control users, trying to convert Monte Carlo results files
on their own computers.

Procedure for full-control users
--------------------------------

.. _`prerequisites for limited-control users (python)`:

Prerequisites - python interpreter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First we need to check if Python interpreter is installed.
Under Linux try if one of following commands (printing Python version) works::

    $ python --version
    $ python3 --version

Under Windows try running the same commands under command line. To start command line under Windows, press
Windows button (or click "Windows" logo in the menu) and type ``cmd``.

At the time of writing Python language interpreter has two popular versions: 2.x (Python 2) and 3.x (Python 3) families.
Command ``python`` invokes either Python 2 or 3, while ``python3`` can invoke only Python 3.

**pymchelper** supports most of the modern Python versions, mainly: 2.7, 3.2, 3.3, 3.4, 3.5 and 3.6.
Check if your interpreter version is supported.

If none of ``python`` and ``python3`` commands are present, then Python interpreter has to be installed.

We suggest to use the newest version available (from 3.x family).

Under Linux the best way is to use your package manager.

* ``apt-get install python3`` (python 3) or ``apt-get install python`` (python 2) for Debian and Ubuntu
* ``dnf install python3`` (python 3) or ``dnf install python`` (python 2) for Fedora
* ``yum install python3`` (python 3) or ``yum install python`` (python 2) for CentOS and SLC

Under Windows the best way is to go to the webpage https://www.python.org/downloads/, download and run the installer.
On the first screen we recommend to mark "Add Python to PATH". The result will be that you will be able to
run python interpreter from command line as any other command. We recommend Windows users to use Python 3.5 or newer.

.. _`single file distribution for limited-control users`:

Single file distribution
~~~~~~~~~~~~~~~~~~~~~~~~

**pymchelper** is shipped as a single file executable.
It can be downloaded from https://github.com/DataMedSci/pymchelper/releases webpage using the web browser.
Command line download for Linux can also be done (here an example with 0.3.6 version,
newer versions should also be available)::

    $ wget https://github.com/DataMedSci/pymchelper/releases/download/v0.3.6/convertmc.pyz -O convertmc

We publish single file executable with .pyz extension, but it can be stripped for a convenience of Linux users.
After downloading the file, make sure it has executable bits set::

    $ chmod ugo+x convertmc

When new version if released, replace downloaded file with newer one.

Now you can start the application under Linux by typing in terminal::

    $ ./convertmc --help

Windows users can simply type::

    $ convertmc.pyz --help

As pymchelper doesn't have any mechanism of automatic updates,
we recommend to use installation using **pip** tool, described below.
It makes easy upgrade and uninstallation procedure.

.. _`prerequisites for limited-control users (pip)`:

Prerequisites - pip tool
~~~~~~~~~~~~~~~~~~~~~~~~

**pip** is a tool for installing and managing Python packages.
It downloads the packages from central Internet repository and installs them
in a similar way as apps are downloaded on your smartphone by Google Play or Apple Store.

Try the following commands (printing pip version)::

    $ pip --version
    $ pip3 --version

In a similar way to python interpreter pip is a tool for Python 2 or 3,
while pip3 works exclusively for Python 3.
If none of these commands are present, then pip has to be installed.

Follow the package installation for your system.
On some systems instructions mentioned below have to be prefixed with `sudo` command.

* ``apt-get install python3-pip`` (python 3) or ``apt-get install python-pip`` (python 2) for Debian and Ubuntu
* ``dnf install python3-pip`` (python 3) or ``dnf install python-pip`` (python 2) for Fedora
* ``yum install python3-pip`` (python 3) or ``yum install python-pip`` (python 2) for CentOS and SLC


Under Windows the best way is to follow User installation method, described here: https://pip.pypa.io/en/stable/installing/


main application - pip package installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now it is time to install **pymchelper** package.
It consists of executable file called `convertmc` and bunch of necessary code files.

Administrator installation is very simple, but requires to save some files in system-wide directories (i.e. `/usr`).
On some systems commands mentioned below have to be prefixed with `sudo` command::

    $ pip install pymchelper

To upgrade the **pymchelper** to newer version, simply type::

    $ pip install --upgrade pymchelper

To completely remove **pymchelper** from your system, use following command::

    $ pip uninstall pymchelper

Now `convertmc` script should be installed for all users and can be invoked by typing::


    $ convertmc --help

Recommended dependencies
~~~~~~~~~~~~~~~~~~~~~~~~

There are two converters which require additional dependencies.

``image`` converter (directly producing PNG images from MC data) needs matplotlib python library, which can be installed
using following command:

::
    $ pip install matplotlib

``tripcube`` converter (producing TRiP98 cube files from MC data) needs pytrip98 python library, which can be installed
using following command:
::

    $ pip install pytrip98

To get more details on pytrip98 installation, go here: https://github.com/pytrip/pytrip/blob/master/INSTALL.rst
Windows version of pytrip98 requires Python 3.5 and prior installation of scipy (we recommend downloading it manually
from http://www.lfd.uci.edu/~gohlke/pythonlibs/#scipy and installing wheel file using pip).

An example session on Ubuntu 16.04 which had python3 and pip3 previously installed:

.. image:: https://asciinema.org/a/a12nd9a9o6fhwpz5zm06nqrxi.png
   :width: 80%
   :target: https://asciinema.org/a/a12nd9a9o6fhwpz5zm06nqrxi?autoplay=1

Procedure for limited-control users
-----------------------------------

Prerequisites - python interpreter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First take a look on `prerequisites for limited-control users (python)`_ to learn how to check if python is installed.

In case Python is missing and you are regular user, the best would be contact somebody with administrator
rights and ask to install Python interpreter in the system.

Installation of Python without administrator rights is possible,
but in case something goes wrong it require expert knowledge.

As an user you will need to download Python interpreter source code (written in C language) and compile it.
For that purpose you will need a C language compiler (i.e. `gcc`) and some other tools (i.e. `make`).
These tools are usually installed by somebody with administrator rights.
Python installer might not complain about missing SSL libraries (i.e. `libssl-dev` under Ubuntu)
and will compile successfully, but we recommend to install it (SSL libraries) before,
to have easier installation of pip package manager in the next steps.

When installing as user under Linux we advice to unpack downloaded source code in `$HOME/tmp` directory and keep it there.
It may be needed for upgrade or deinstallation purpose.

Let us install Python 2.7 for Linux into `$HOME/usr/py27` directory. First let us create `$HOME/tmp` directory and step into it::

    $ mkdir -p $HOME/tmp
    $ cd $HOME/tmp

Now its time to download and unpack source code package. We show an example with 2.7.12 version, but newer one can
be problably found on https://www.python.org/downloads/source/ ::

    $ wget https://www.python.org/ftp/python/2.7.12/Python-2.7.12.tgz
    $ tar -zxf Python-2.7.12.tgz
    $ cd Python-2.7.12

Finally let us start compilation process (it might take couple of minutes). This process might be interrupted by
some error message. Do not hesitate to find a professional help to fix it::

    $ ./configure --prefix=$HOME/usr/py27
    $ make
    $ make install

Python2.7 is now installed into `$HOME/usr/py27` directory.
In order to execute python interpreter, you need to provide full path to the executable file, i.e.::

    $ $HOME/usr/py27/bin/python --version

In a similar way python3.x can be installed.

User installation for Windows is not covered by this document.

Single file distribution
~~~~~~~~~~~~~~~~~~~~~~~~

Single file distribution is the same as for full-control users, see `single file distribution for limited-control users`_.

Prerequisites - pip tool
~~~~~~~~~~~~~~~~~~~~~~~~

First take a look on `prerequisites for limited-control users (pip)`_ to learn how to check if pip is installed.

If none of these commands are present, then pip has to be installed.

Follow the instruction from here https://pip.pypa.io/en/stable/installing/,
mainly - download installation script using your web browser, or by typing in the terminal (in case using Linux)::

    $ wget https://bootstrap.pypa.io/get-pip.py

Now use your python interpreter to execute downloaded script. It will install pip in your home directory::

    $ python get-pip.py --user

Try if pip command is available by typing::

    $ $HOME/.local/bin/pip --version

If this method fails you can also try to use a `ensurepip` approach.
It works with Python versions: 2.7 (starting from 2.7.9), 3.4 and newer.
To install pip, simply type::

    $ python -m ensurepip

Similar method can be used for Windows.

main application - pip package installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now it is time to install **pymchelper** package.
It consists of executable file called `convertmc` and bunch of necessary code files.

User installation will put the **pymchelper** under some hidden directory (for Linux it will be `$HOME/.local`,
for Windows it might be `%userprofile%\appdata\roaming\python\python35\Scripts` or other)

To install the package, type in the terminal::

    $ pip install pymchelper --user

If `pip` command is missing on your system, replace `pip` with `pip3` in abovementioned instruction.

To upgrade the **pymchelper** to newer version, simply type::

    $ pip install --upgrade pymchelper --user

To completely remove **pymchelper** from your system, use following command::

    $ pip uninstall pymchelper

In most of modern systems all executables found in `$HOME/.local/bin` (or equivalent) directory
(`convertmc` executable will be saved there) can be called like normal commands (i.e. `pwd`, `cd`).
It means that after installation you should be able to simply type in terminal: `convertmc` to use this package ::

    $ convertmc --help

If this is not the case, please prefix the command with the directory it was saved and call it in the following way::

    $ $HOME/.local/bin/convertmc --help

or for Windows::

    $ %userprofile%\appdata\roaming\python\python35\Scripts\convertmc --help


Recommended dependencies
~~~~~~~~~~~~~~~~~~~~~~~~

There are two converters which require additional dependencies.

``image`` converter (directly producing PNG images from MC data) needs matplotlib python library, which can be installed
using following command:

::
    $ pip install matplotlib --user

``tripcube`` converter (producing TRiP98 cube files from MC data) needs pytrip98 python library, which can be installed
using following command:
::

    $ pip install pytrip98 --user

Right now the installation requires compilation of C extension which leads to complex compilation. Only for experts.
It is better to wait until this issue: https://github.com/pytrip/pytrip/issues/89 is fixed.