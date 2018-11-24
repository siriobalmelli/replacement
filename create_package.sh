#!/bin/bash

set -e

# Clean up previous packages
rm -rfv build dist replacement.egg-info

# muss pass tests
./run-tests.sh

# generate README
./gen_readme.sh

# Create package
python3 setup.py sdist bdist_wheel

cat <<EOF

##
# build successful
##

# submit to pypi.org:
twine upload dist/*

# submit to test.pypi.org:
twine upload --repository-url https://test.pypi.org/legacy/ dist/*
# install from 'test' on a machine with pip3
python3 -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.python.org/pypi  replacement
EOF
