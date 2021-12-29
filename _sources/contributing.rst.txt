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
We assume you are familiar with GIT source control system. If not you will
other instruction at the end of this page.

1. Fork the ``pymchelper`` repo on GitHub.
2. Clone your fork locally::

    $ git clone git@github.com:your_name_here/pymchelper.git

3. If you are not familiar with GIT, proceed to step 5, otherwise create a branch for local development::

    $ cd pymchelper
    $ git checkout -b feature/issue_number-name_of_your_bugfix_or_feature

4. Now you can make your changes locally.

As the software is prepared to be shipped as pip package, some modifications
of PYTHONPATH variables are needed to run the code. Let us assume you are now in the same directory as ``setup.py`` file.


The standard way to execute Python scripts WILL NOT WORK. What users see as convertmc program, is basically pymchelper/run.py script::

   $ python pymchelper/run.py --help

To have the code working, the PYTHONPATH has to be adjusted::

   $ PYTHONPATH=. python pymchelper/run.py --help
    usage: run.py [-h] [-V] converter ...
    (...)
    

5. Make local changes to fix the bug or to implement a feature.

6. When you're done making changes, check that your changes comply with PEP8 code quality standards (flake8 tests) and run unit tests with pytest::

    $ flake8 pymchelper tests
    $ pytest tests

   To get flake8 and pytest, just pip install them.

7. Commit your changes and push your branch to GitHub::

    $ git add .
    $ git commit -m "Your detailed description of your changes."

8. Repeat points 4-6 until the work is done. Now its time to push the changes to remote repository::

    $ git push origin feature/issue_number-name_of_your_bugfix_or_feature

9. Submit a pull request through the GitHub website to the master branch of ``git@github.com:DataMedSci/pymchelper.git`` repository.

10. Check the status of automatic tests. In case some of the tests fails, fix the problem. Then commit and push your changes (steps 5-8).


Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. 
   Put your new functionality into a function with a docstring, and extend the documentation where necessary.
3. Make sure that all tests triggered by the Pull Requests are passing.

Tips
----

To run full tests type::

   pytest tests/

To run only a single test type::

   pytest tests/test_file_to_run.py

.. _`bugs`: https://github.com/DataMedSci/pymchelper/issues
.. _`features`: https://github.com/DataMedSci/pymchelper/issues