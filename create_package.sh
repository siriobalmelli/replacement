#!/bin/bash

# Clean up previous packages
rm -rfv build dist replacement.egg-info

# Create package
python3 setup.py sdist bdist_wheel

# # submit to test.pypi.org:
# twine upload --repository-url https://test.pypi.org/legacy/ dist/*
# # test install on a machine with pip3
# python3 -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.python.org/pypi  replacement
