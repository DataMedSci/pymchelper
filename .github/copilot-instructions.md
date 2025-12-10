# GitHub Copilot Instructions for pymchelper

## Project Overview

**pymchelper** is a Python toolkit for working with particle transport codes such as FLUKA and SHIELD-HIT12A. It reads binary outputs from Monte Carlo simulations and helps users convert, analyze, and visualize results on any platform (Linux, Windows, macOS).

### Key Features
- Convert binary outputs to plots and common formats (CSV, XLS, HDF5)
- Speed up simulations by splitting and merging runs
- Python library for loading simulation results into convenient objects
- Command-line tools: `convertmc`, `runmc`, `mcscripter`, `plan2sobp`

### Technology Stack
- **Language**: Python 3.9-3.14
- **Build System**: setuptools with setuptools-scm for versioning
- **Key Dependencies**: numpy (core), matplotlib (imaging), h5py (HDF5), pydicom (DICOM), xlwt (Excel)
- **Testing**: pytest with pytest-rerunfailures
- **Code Quality**: flake8 for linting, yapf for formatting
- **Documentation**: Sphinx with pydata-sphinx-theme

## Repository Structure

```
pymchelper/
├── pymchelper/          # Main package source code
│   ├── run.py          # Entry point for convertmc CLI
│   ├── readers/        # Binary file readers for different formats
│   ├── writers/        # Output format writers (CSV, HDF5, Excel, etc.)
│   ├── utils/          # Utilities including runmc, mcscripter
│   ├── flair/          # FLUKA-related functionality
│   └── shieldhit/      # SHIELD-HIT12A-related functionality
├── tests/              # Test suite with pytest
│   ├── res/           # Test resources and sample data files
│   ├── integration/   # Integration tests
│   └── test_*.py      # Unit tests
├── docs/               # Sphinx documentation
├── examples/           # Usage examples
└── pyproject.toml      # Project configuration
```

## Development Setup

### Setting Up Your Environment

1. Clone the repository and create a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install in editable mode with all dependencies:
```bash
pip install --upgrade pip
pip install -e .[full,test]
```

The `[full,test]` extras install all features plus testing dependencies.

### Building and Testing

**Run all tests:**
```bash
pytest
```

**Run only fast tests (smoke tests):**
```bash
pytest -m smoke
```

**Run tests excluding slow ones:**
```bash
pytest -m "not slow"
```

**Check code quality with flake8:**
```bash
flake8 pymchelper tests
```

**Format code with yapf:**
```bash
yapf -ir pymchelper tests
```

**Build documentation:**
```bash
cd docs && make html
```

## Coding Standards and Conventions

### Python Style
- Follow **PEP 8** style guide
- Maximum line length: **120 characters** (configured in `.flake8`)
- Use **yapf** for code formatting (configured in `pyproject.toml`)
- Column limit: 120, based on PEP 8 style

### Code Quality
- All code must pass **flake8** checks before merging
- Critical syntax errors are checked automatically in CI
- Use **pre-commit** hooks for automatic formatting (see `.pre-commit-config.yaml`)

### Testing
- Add tests for all new functionality
- Tests should be in `tests/` directory with `test_*.py` naming
- Use pytest markers:
  - `@pytest.mark.smoke` for fast smoke tests
  - `@pytest.mark.slow` for longer-running tests
- Test resources should go in `tests/res/` directory

### Documentation
- Add docstrings to new functions/classes following existing patterns
- Update relevant documentation in `docs/` directory for user-facing changes
- Use reStructuredText (.rst) format for documentation files
- Build docs with `make html` in the docs directory to verify changes

### Commit Messages
- Write clear commit messages explaining **why** the change was made, not just what
- Reference issue numbers in commits: `"Fix issue #123: Brief description"`
- Follow conventional commit style when possible

### Branch Naming
- Use pattern: `feature/issue_number-name_of_your_bugfix_or_feature`
- Example: `feature/456-add-csv-export`

## Important Notes for Development

### File Formats and Readers
- The package reads binary output files from FLUKA (*_fort.* pattern) and SHIELD-HIT12A (.bdo)
- Each simulator has its own reader in `pymchelper/readers/`
- Test data files are stored in `tests/res/` with subdirectories for different formats

### CLI Entry Points
- `convertmc`: Main tool for converting binary outputs (defined in `pymchelper/run.py`)
- `runmc`: Tool for parallel simulation runs (defined in `pymchelper/utils/runmc.py`)
- `mcscripter`: Script generation tool (defined in `pymchelper/utils/mcscripter.py`)
- `plan2sobp`: Radiotherapy planning tool (defined in `pymchelper/utils/radiotherapy/plan.py`)

### Versioning
- Uses **setuptools-scm** for automatic versioning from git tags
- Version is written to `pymchelper/_version.py` during build
- Use post-release versioning scheme

### Platform Support
- Must work on Linux, macOS, and Windows
- CI tests on all three platforms with Python 3.9-3.14
- Be mindful of path separators and platform-specific issues

### Dependencies Management
- Core dependencies should be minimal (mainly numpy)
- Optional features use extras_require: `[image]`, `[excel]`, `[hdf]`, `[dicom]`, `[full]`
- Test dependencies are in `[test]` extra
- Development dependencies in `[dev]` extra

## CI/CD and Automation

### GitHub Actions
- Tests run automatically on Python 3.9, 3.10, 3.11, 3.12, 3.13, 3.14
- Tests run on Linux, macOS, and Windows
- Flake8 syntax checks run automatically
- All checks must pass before merging

### Pre-commit Hooks
- Configured in `.pre-commit-config.yaml`
- Includes: trailing whitespace removal, end-of-file fixer, YAML checker, yapf formatting
- Install with: `pre-commit install`

## Pull Request Guidelines

1. **Include tests**: Cover your changes with appropriate tests
2. **Update documentation**: Add/update docstrings and documentation files
3. **Pass CI checks**: Ensure all automated tests pass on all platforms and Python versions
4. **Follow code style**: Use yapf for formatting, ensure flake8 passes
5. **Keep commits clean**: Write clear, descriptive commit messages
6. **Link to issues**: Reference relevant issue numbers in PR description (e.g., "Fixes #123")

## Common Tasks

### Adding a New Converter
1. Create a new writer in `pymchelper/writers/`
2. Register it in the appropriate converter configuration
3. Add tests in `tests/` with sample output verification
4. Update documentation in `docs/` with usage examples

### Adding Support for a New File Format
1. Create a new reader in `pymchelper/readers/`
2. Add sample test files to `tests/res/`
3. Write tests verifying correct parsing
4. Update documentation with format details and examples

### Running the CLI Tools Locally
After installing in editable mode, you can run:
```bash
convertmc --help
runmc --help
mcscripter --help
plan2sobp --help
```

## Additional Resources

- **Project Site**: https://datamedsci.github.io/pymchelper/
- **Getting Started**: https://datamedsci.github.io/pymchelper/getting_started.html
- **User's Guide**: https://datamedsci.github.io/pymchelper/user_guide.html
- **Issues**: https://github.com/DataMedSci/pymchelper/issues
- **Changelog**: https://github.com/DataMedSci/pymchelper/releases

## License

pymchelper is licensed under the MIT License.
