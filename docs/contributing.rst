.. highlight:: bash

.. role:: bash(code)
   :language: bash

Contributing Guide
==================

Contributions are welcome, and they are greatly appreciated! 
Every little bit helps, and credit will always be given.

You can contribute in many ways:

Types of Contributions
----------------------

Report Bugs or propose features
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The best way to report a bug is to login to your Github account and fill the form at https://github.com/DataMedSci/pymchelper/issues 

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

Fix Bugs or Implement Features
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for bugs or features.
Anything tagged with "bug" or "feature" is open to whoever wants to implement it.

Write Documentation
~~~~~~~~~~~~~~~~~~~

`pymchelper` could always use more documentation, whether as part of the
official `pymchelper` docs, in docstrings, or even on the web in blog posts,
articles, and such.


Get Started for developers
--------------------------

Ready to contribute? Here's how to set up `pymchelper` for local development.
We assume you are familiar with GIT source control system.

1. Fork the ``pymchelper`` repo on GitHub.

2. Clone your fork locally::

    git clone git@github.com:your_name_here/pymchelper.git

   Then navigate to the directory::

    cd pymchelper

3. Create a branch for local development::

    git checkout -b feature/issue_number-name_of_your_bugfix_or_feature

4. Create a dedicated virtual environment::

    python3 -m venv .venv

   Activate it::

    source .venv/bin/activate

   Upgrade pip and install the package in editable mode with all dependencies::

    pip install --upgrade pip
    pip install -e .[full,test]

   On Windows, activate the virtual environment with::

    .venv\Scripts\activate

   The ``[full,test]`` extras install all features plus testing dependencies (pytest, flake8, etc.).

5. Make your changes to fix the bug or implement a feature.

6. Run the test suite to verify your changes::

    pytest

   To run only fast tests (smoke tests)::

    pytest -k "smoke"

   To run tests excluding slow ones::

    pytest -k "not slow"

   The project uses ``flake8`` for code quality checks. Critical syntax errors are checked automatically in CI.

7. If you're adding new functionality, add tests to cover it.

8. If you're changing user-facing behavior, update the documentation in the ``docs/`` directory.

9. Stage your changes::

    git add .

   Commit with a clear message::

    git commit -m "Fix issue #123: Brief description of your changes"

10. Push your branch to GitHub:

    ::

     git push origin feature/issue_number-name_of_your_bugfix_or_feature

11. Submit a pull request through the GitHub website to the ``master`` branch.

12. GitHub Actions will automatically run tests on multiple Python versions (3.9-3.14) and platforms (Linux, macOS, Windows). Check the status and fix any failures by pushing additional commits to your branch.


Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. **Include tests**: The pull request should include tests that cover your changes.
   
2. **Update documentation**: If the pull request adds functionality:
   
   - Add docstrings to new functions/classes following existing patterns
   - Update relevant documentation in ``docs/`` directory
   - If adding a new converter or major feature, add usage examples

3. **Pass CI checks**: Ensure all automated tests pass on:
   
   - All supported Python versions (3.9, 3.10, 3.11, 3.12, 3.13, 3.14)
   - All platforms (Linux, macOS, Windows)
   - Flake8 syntax checks

4. **Follow code style**: Use consistent formatting with the existing codebase. The project uses yapf for formatting (configured in ``pyproject.toml``).

5. **Keep commits clean**: Write clear commit messages that explain *why* the change was made, not just *what* changed.

6. **Link to issues**: Reference relevant issue numbers in your PR description (e.g., "Fixes #123").

Tips
----

**Running tests:**

Run all tests::

   pytest

Run tests from a specific file::

   pytest tests/test_example.py

Run a specific test function::

   pytest tests/test_example.py::test_function_name

Run tests matching a pattern::

   pytest -k "test_pattern"

Run with verbose output::

   pytest -v

Run with automatic retries (useful for flaky tests)::

   pytest --reruns 2

**Development dependencies:**

All development dependencies are defined in ``pyproject.toml``:

- ``[test]`` - Testing tools (pytest, flake8, etc.)
- ``[full]`` - All optional features (image, excel, hdf converters, etc.)
- ``[dev]`` - Development tools (includes test + full + build tools)
- ``[docs]`` - Documentation building tools (Sphinx, themes)

Install everything for development::

   pip install -e .[dev]

**Building documentation locally:**

For instructions on building and viewing documentation locally, see the :doc:`Technical Documentation </technical>` section on "Preparing sphinx documentation".

.. _`bugs`: https://github.com/DataMedSci/pymchelper/issues
.. _`features`: https://github.com/DataMedSci/pymchelper/issues