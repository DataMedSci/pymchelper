# Quick Start Guide - Modern pymchelper Development

This guide covers the essential commands for working with pymchelper's new pyproject.toml-based setup.

## Prerequisites

- Python 3.9 or higher
- Git (for version detection)
- pip 21.3+ (for pyproject.toml support)

## Installation

### For Users

```bash
# Install from PyPI with all features
pip install pymchelper[full]

# Install specific extras
pip install pymchelper[image]     # Just matplotlib
pip install pymchelper[hdf]       # Just HDF5 support
pip install pymchelper[dicom]     # Just DICOM support
```

### For Developers

```bash
# Clone repository
git clone https://github.com/DataMedSci/pymchelper.git
cd pymchelper

# Install in editable mode with all dependencies
pip install -e .[dev]

# Or just install with test dependencies
pip install -e .[full,test]
```

## Common Commands

### Running Tests

```bash
# Run all tests
pytest

# Run fast tests only (skip slow ones)
pytest -k "not slow"

# Run smoke tests
pytest -k "smoke"

# Run slow tests
pytest -k "slow"

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_averaging.py
```

### Code Quality

```bash
# Check code style with flake8
flake8 pymchelper tests examples

# Format code with yapf
yapf -i pymchelper/**/*.py

# Run pre-commit hooks
pre-commit run --all-files
```

### Building Packages

```bash
# Install build tool
pip install build

# Build wheel and source distribution
python -m build

# Check packages with twine
pip install twine
twine check dist/*

# View package contents
tar -tzf dist/pymchelper-*.tar.gz | head -20
unzip -l dist/pymchelper-*.whl | head -20
```

### Version Information

```bash
# Check current version (from git tags)
python -c "from setuptools_scm import get_version; print(get_version())"

# Check version of installed package
python -c "import pymchelper; print(pymchelper.__version__)"

# Check version via command line tool
convertmc --version
```

### Creating Releases

```bash
# 1. Ensure all tests pass
pytest

# 2. Create and push tag
git tag v1.2.3
git push origin v1.2.3

# 3. GitHub Actions automatically:
#    - Runs full test suite on all platforms
#    - Builds packages
#    - Publishes to PyPI
#    - Creates Windows executables
#    - Updates documentation
```

## Development Workflow

### Initial Setup

```bash
# 1. Clone and enter directory
git clone https://github.com/DataMedSci/pymchelper.git
cd pymchelper

# 2. Create virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install in development mode
pip install -e .[dev]

# 4. Install pre-commit hooks (optional but recommended)
pre-commit install
```

### Daily Development

```bash
# 1. Make changes to code
# 2. Run tests frequently
pytest -k "not slow"

# 3. Check code style
flake8 pymchelper

# 4. Commit changes
git add .
git commit -m "Your change description"

# 5. Push to GitHub
git push
```

### Before Pull Request

```bash
# 1. Run all tests
pytest

# 2. Check code style
flake8 pymchelper tests examples

# 3. Format code if needed
yapf -i pymchelper/**/*.py

# 4. Build documentation (optional)
cd docs
pip install -r requirements.txt
sphinx-build . _build

# 5. Build package to verify
python -m build
```

## Troubleshooting

### "No module named 'setuptools_scm'"

```bash
pip install setuptools-scm>=8
```

### Version shows "0.0.0"

```bash
# Fetch git tags
git fetch --tags

# Verify tags exist
git tag -l

# Check git describe works
git describe --tags --long
```

### Import errors after installation

```bash
# Reinstall in development mode
pip install -e .[dev]
```

### Build fails

```bash
# Ensure build dependencies are installed
pip install build setuptools>=64 setuptools-scm>=8

# Clean old build artifacts
rm -rf build/ dist/ *.egg-info

# Try building again
python -m build
```

### Tests fail

```bash
# Ensure test dependencies are installed
pip install -e .[test]

# Check Python version
python --version

# Run with verbose output
pytest -v
```

## VS Code Tasks

The project includes VS Code tasks for common operations:

- **Run tests (pyproject.toml)** - Runs pytest with modern setup
- **Run tests (legacy)** - Runs pytest with old requirements.txt

Access via: `Ctrl+Shift+P` → "Tasks: Run Task"

## Environment Variables

### For Version Detection

```bash
# Override version for testing
export SETUPTOOLS_SCM_PRETEND_VERSION=1.2.3
python -c "from setuptools_scm import get_version; print(get_version())"
```

### For PyInstaller

```bash
# Ensure VERSION file exists before building executables
python -c "from setuptools_scm import get_version; print(get_version())" > pymchelper/VERSION
```

## Package Structure

```
pymchelper/
├── pyproject.toml          # Main configuration (NEW)
├── setup.py                # Legacy support (deprecated)
├── setup.cfg               # Legacy support (deprecated)
├── README.md               # Project documentation
├── MIGRATION_GUIDE.md      # Detailed migration information
├── MIGRATION_SUMMARY.md    # Migration summary
├── requirements.txt        # Points to .[full]
├── pymchelper/            # Main package
│   ├── __init__.py
│   ├── VERSION            # Auto-generated by setuptools-scm
│   └── ...
├── tests/                 # Test suite
│   ├── requirements-test.txt  # Points to .[test]
│   └── ...
└── docs/                  # Documentation
    └── ...
```

## Additional Resources

- **Full Documentation**: https://datamedsci.github.io/pymchelper/
- **Migration Guide**: [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)
- **GitHub Issues**: https://github.com/DataMedSci/pymchelper/issues
- **PyPI Package**: https://pypi.org/project/pymchelper/

## Getting Help

1. Check [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) for detailed migration information
2. Read the documentation at https://datamedsci.github.io/pymchelper/
3. Search existing issues at https://github.com/DataMedSci/pymchelper/issues
4. Open a new issue if needed

---

**Note**: This guide reflects the modern pyproject.toml-based setup. For legacy setup.py usage, see MIGRATION_GUIDE.md.
