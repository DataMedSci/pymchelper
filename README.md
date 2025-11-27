# pymchelper

**pymchelper** is a toolkit for aiding users of the particle transport codes, such as [FLUKA](http://fluka.cern/) and [SHIELD-HIT12A](https://shieldhit.org/).
Particle transport codes produce binary files (especially when running on dedicated computing clusters).
It provides a command line program `convertmc` which can convert these binary files to graphs:

```
convertmc image --many "*.bdo"
```

<p float="left">
  <img src="/docs/default_1d.png" width="30%" />
  <img src="/docs/default_2d.png" width="30%" />
</p>

This converter is capable of converting binary output to many other formats, like CSV, XLS or HDF.

Another feature of the toolkit is a command line utility `runmc` which speeds up particle transport simulation by splitting the calculation on multiple processes and merging the results

```
runmc --jobs 16 --out-type txt directory_with_input_files
```

Toolkit can also serve as a library in Python language, which can be used by programmers and data scientists to read data from binary files into convenient Python objects. This allows further data processing using other Python tools and libraries.

**pymchelper** works under Linux, Windows and Mac OSX operating systems.

## Installation

To install **pymchelper** as a python package, type:

```
pip install pymchelper[full]
```

On Debian-based Linux systems (Debian 8+ or Ubuntu 16.04+), **pymchelper** can be installed using `apt` package manager with couple of commands::

```bash
wget --quiet --output-document - https://datamedsci.github.io/deb_package_repository/public.gpg | sudo apt-key add -
```
```bash
sudo wget --quiet --output-document /etc/apt/sources.list.d/datamedsci.list https://datamedsci.github.io/deb_package_repository/datamedsci.list
```
```bash
sudo apt update
```
```bash
sudo apt install pymchelper
```

## Documentation

---

Full pymchelper documentation can be found here: https://datamedsci.github.io/pymchelper/index.html

See [Getting Started](https://datamedsci.github.io/pymchelper/getting_started.html) for installation and basic information, and the [User&#39;s Guide](https://datamedsci.github.io/pymchelper/user_guide.html) for an overview of how to use the project.

## Development

**pymchelper** uses modern Python packaging with `pyproject.toml`. The project supports Python 3.9-3.14.

### Quick Start

```bash
# Clone the repository
git clone https://github.com/DataMedSci/pymchelper.git
cd pymchelper

# Install in editable mode with all dependencies
pip install -e .[dev]

# Run tests
pytest
```

### Building from Source

```bash
# Install build tools
pip install build

# Build wheel and source distribution
python -m build

# Install the built package
pip install dist/pymchelper-*.whl
```

### Version Management

This project uses `setuptools-scm` for automatic versioning based on git tags:
- Release versions are created by tagging: `git tag v1.2.3`
- Development versions automatically append `+revN` based on commits since the last tag

For more details, see [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) for the transition from `setup.py` to `pyproject.toml`.
