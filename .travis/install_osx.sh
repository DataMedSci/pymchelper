#!/usr/bin/env bash

set -x # Print command traces before executing command

set -e # Exit immediately if a simple command exits with a non-zero status.

set -o pipefail # Return value of a pipeline as the value of the last command to
                # exit with a non-zero status, or zero if all commands in the
                # pipeline exit successfully.

# file inspired by https://github.com/pyca/cryptography

# MacOSX hav Python 2.7 installed by default, lets use it. We just need to install pip
if [[ $TOXENV == py27* ]] ;
then
    curl -O https://bootstrap.pypa.io/get-pip.py
    python get-pip.py --user
    pip install --user --upgrade pip
    pip install --user --upgrade virtualenv
    pip install --user --upgrade tox
fi

# At this point we run default Python 2.7 interpreter
# versioneer doesn't support Python 3.2, so we run it now with current interpreter
# for other interpreters pointed out by TOXENV look at the end of the script
pip install --user --upgrade versioneer
~/Library/Python/2.7/bin/versioneer install

# For native python 2.7 we can jump out
if [[ $TOXENV == py27* ]] ; then exit 0; fi


# For Python 3, first install pyenv
brew update || brew update
brew unlink pyenv && brew install pyenv && brew link pyenv

# setup pyenv
PYENV_ROOT="$HOME/.pyenv"
PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

# install Python 3.x
# TODO find the way to make it faster (use pre-installed python versions on travis?)
# this is most time-consuming issue, now takes about 2 min
case "${TOXENV}" in
        py32*)
            pyenv install -s 3.2
            pyenv global 3.2
            ;;
        py33*)
            pyenv install -s 3.3.6
            pyenv global 3.3.6
            ;;
        py34*)
            pyenv install -s 3.4.4
            pyenv global 3.4.4
            ;;
        py35*)
            pyenv install -s 3.5.1
            pyenv global 3.5.1
            ;;
        py36*)
            pyenv install -s 3.6-dev
            pyenv global 3.6-dev
            ;;
        *)
            exit 1
esac

# TODO comment needed
pyenv rehash

# install virtualenv and tox ($VENVVER and $PIPVER is set only for python 3.2)
pyenv exec pip install --upgrade virtualenv$VENVVER pip$PIPVER tox

pyenv exec pip install -r requirements.txt
