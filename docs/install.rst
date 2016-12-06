.. highlight:: shell

Detailed Installation Guide
===========================
Installation guide is divided in two phases: checking the prerequisites and main package installation.


Prerequisites
-------------

**pymchelper** works under Windows, Linux and Mac OSX operating systems.

First we need to check if Python interpreter is installed.
Try if one of following commands (printing Python version) works::

    python --version
    python3 --version

At the time of writing Python language interpreter has two popular versions: 2.x (Python 2) and 3.x (Python 3) families.
Command ``python`` invokes either Python 2 or 3, while ``python3`` can invoke only Python 3.

**pymchelper** supports most of the modern Python versions, mainly: 2.7, 3.2, 3.3, 3.4, 3.5 and 3.6.
Check if your interpreter version is supported.

If none of ``python`` and ``python3`` commands are present, then Python interpreter has to be installed.

We suggest to use the newest version available (from 3.x family).

Python installers can be found at the python web site (http://python.org/download/).

pymchelper also relies on these packages:

  * `NumPy <http://www.numpy.org/>`_ -- Better arrays and data processing.
  * `matplotlib <http://matplotlib.org/>`_ -- Needed for plotting, optional.

and if they are not installed beforehand, these will automatically be fetched by pip.

Installing using pip (all platforms)
------------------------------------

The easiest way to install PyTRiP98 is using `pip <https://pypi.python.org/pypi/pip>`_::

.. note::
    Starting from mid-2014 pip comes pre-installed with Python newer than 3.4 and 2.7.9 (for 2.x family)


Administrator installation (root access)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Administrator installation is very simple, but requires to save some files in system-wide directories (i.e. `/usr`)::

    sudo pip install pymchelper

To upgrade the **pymchelper** to newer version, simply type::

    sudo pip install --upgrade pymchelper

To completely remove **pymchelper** from your system, use following command::

    sudo pip uninstall pymchelper

Now all **pymchelper** commands should be installed for all users::

    convertmc --help


User installation (non-root access)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

User installation will put the **pymchelper** under hidden directory `$HOME/.local`.

To install the package, type in the terminal::

    pip install pymchelper --user

If `pip` command is missing on your system, replace `pip` with `pip3` in abovementioned instruction.

To upgrade the **pymchelper** to newer version, simply type::

    pip install --upgrade pymchelper --user

To completely remove **pymchelper** from your system, use following command::

    pip uninstall pymchelper

In most of modern systems all executables found in `$HOME/.local/bin` directory can be called
like normal commands (i.e. `ls`, `cd`). It means that after installation you should be able
to simply type in terminal::

    convertmc --help

If this is not the case, please prefix the command with `$HOME/.local/bin` and call it in the following way::

    $HOME/.local/bin/convertmc --help

