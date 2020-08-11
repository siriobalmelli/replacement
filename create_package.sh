#!/bin/bash

set -e

# Clean up previous packages
python setup.py clean --all
rm dist/*

# generate README
python -m replacement -t README.yaml >README.md

# Create package
python setup.py sdist bdist_wheel

# muss pass tests
pytest

cat <<EOF

##
# build successful
##

# submit to pypi.org:
twine upload dist/*

# submit to test.pypi.org:
twine upload --repository-url https://test.pypi.org/legacy/ dist/*
# install from 'test' on a machine with pip3
python3 -m pip install --force-reinstall --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.python.org/pypi replacement
EOF
