#!/usr/bin/env bash

set -x # Print command traces before executing command

set -e # Exit immediately if a simple command exits with a non-zero status.

set -o pipefail # Return value of a pipeline as the value of the last command to
                # exit with a non-zero status, or zero if all commands in the
                # pipeline exit successfully.

# file inspired by https://github.com/pyca/cryptography

brew update || brew update

brew outdated openssl || brew upgrade openssl
brew install openssl@1.1

# install pyenv
git clone --depth 1 https://github.com/pyenv/pyenv ~/.pyenv
PYENV_ROOT="$HOME/.pyenv"
PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

case "${TOXENV}" in
        py27)
            curl -O https://bootstrap.pypa.io/get-pip.py
            python get-pip.py --user
            ;;
        py34)
            pyenv install 3.4.6
            pyenv global 3.4.6
            ;;
        py35)
            pyenv install 3.5.3
            pyenv global 3.5.3
            ;;
        py36)
            pyenv install 3.6.1
            pyenv global 3.6.1
            ;;
esac
pyenv rehash

# install virtualenv and tox
if [[ $TOXENV == py27* ]] ;
then
    PATH="$HOME/Library/Python/2.7/bin:$PATH"
    pip install --user --upgrade virtualenv pip tox
    pip install --user -r requirements.txt
    pip install --user versioneer
    versioneer install
else
    pyenv exec pip install --upgrade virtualenv pip tox
    pyenv exec pip install -r requirements.txt
    pyenv exec pip install versioneer
    pyenv exec versioneer install
fi
