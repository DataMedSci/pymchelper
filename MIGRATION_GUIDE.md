# Migration Guide: setup.py → pyproject.toml

This project has been migrated from `setup.py` to modern `pyproject.toml` configuration.

## What Changed

### 1. **Configuration Files**
- ✅ **NEW**: `pyproject.toml` - Single source of truth for all project configuration
- ⚠️ **DEPRECATED**: `setup.py` and `setup.cfg` - Kept for backwards compatibility only

### 2. **Dynamic Versioning**
- **Before**: Custom `version.py` with git describe logic
- **After**: `setuptools-scm` automatically versions from git tags
- Version format: `v1.2.3` tag → `1.2.3` package version
- Development commits: `v1.2.3-5-gabcd1234` → `1.2.3+rev5`

### 3. **Python Version Support**
- **Supported**: Python 3.9, 3.10, 3.11, 3.12, 3.13, 3.14
- **Numpy compatibility** automatically handled based on Python version

### 4. **GitHub Actions**
- **Testing**: All Python versions (3.9-3.13) on Linux, macOS, and Windows
- **Release**: Uses modern `python -m build` instead of `setup.py bdist_wheel`
- **Executables**: PyInstaller workflow updated for dynamic versioning

## For Users

### Installation (No Changes Required)
```bash
# Standard installation still works the same
pip install pymchelper

# From source
git clone https://github.com/DataMedSci/pymchelper.git
cd pymchelper
pip install .

# With all optional dependencies
pip install .[full]

# For development
pip install -e .[full,test]
```

### Optional Dependencies
All extras are defined in `pyproject.toml`:
- `[image]` - matplotlib for plotting
- `[excel]` - xlwt for Excel export
- `[hdf]` - h5py for HDF5 support
- `[dicom]` - pydicom and scipy for DICOM
- `[pytrip]` - pytrip98 for treatment planning
- `[full]` - All optional dependencies
- `[test]` - Testing and development tools
- `[dev]` - Full development environment

## For Developers

### Building Packages
```bash
# Install build tools
pip install build

# Build wheel and source distribution
python -m build

# Check package
pip install twine
twine check dist/*
```

### Version Management
```bash
# Version is automatically determined from git tags
git tag v1.2.3
python -m build  # Creates pymchelper-1.2.3.tar.gz

# For development versions (between releases)
# setuptools-scm automatically appends +revN based on commits since last tag
```

### Creating Releases
1. Create and push a version tag: `git tag v1.2.3 && git push origin v1.2.3`
2. GitHub Actions automatically:
   - Runs tests on all Python versions and OSes
   - Builds packages
   - Publishes to PyPI
   - Creates Windows executables
   - Generates documentation

### Running Tests Locally
```bash
# Install with test dependencies
pip install -e .[full,test]

# Run tests
pytest

# Specific test markers
pytest -k "smoke"      # Fast smoke tests
pytest -k "not slow"   # Skip slow tests
pytest -k "slow"       # Only slow tests
```

### Development Environment Setup
```bash
# Clone repository
git clone https://github.com/DataMedSci/pymchelper.git
cd pymchelper

# Install in editable mode with all dependencies
pip install -e .[dev]

# Install pre-commit hooks (optional)
pre-commit install
```

## Backwards Compatibility

### Deprecated Files (Still Work, But Not Recommended)
- `setup.py` - Shows deprecation warning, redirects to pyproject.toml
- `setup.cfg` - Tool configs moved to pyproject.toml
- `requirements.txt` - Now references `.[full]` from pyproject.toml
- `tests/requirements-test.txt` - Now references `.[test]` from pyproject.toml

### Removed Dependencies
- No standalone `pymchelper/version.py` execution needed
- `setuptools-scm` handles all versioning automatically

## CI/CD Changes

### GitHub Actions Workflows Updated
1. **`.github/workflows/python-app.yml`**
   - Tests Python 3.9-3.13 on ubuntu-latest, macos-latest, windows-latest
   - Uses `pip install -e .[full,test]` instead of requirements.txt

2. **`.github/workflows/release-pip.yml`**
   - Uses `python -m build` instead of `setup.py bdist_wheel`
   - Properly fetches full git history for version determination

3. **`.github/workflows/release-win-exe.yml`**
   - Generates VERSION file using setuptools-scm
   - PyInstaller bundles updated for dynamic versioning

## Troubleshooting

### "No module named 'setuptools_scm'"
```bash
pip install setuptools-scm>=8
```

### Version shows "0.0.0"
This happens when git tags are not available:
```bash
# Ensure you have git history
git fetch --tags --unshallow

# Verify tags exist
git tag -l
```

### Import errors after migration
```bash
# Reinstall package in development mode
pip install -e .[full,test]
```

## Questions?

- Open an issue: https://github.com/DataMedSci/pymchelper/issues
- Check documentation: https://datamedsci.github.io/pymchelper/
