#!/bin/bash

# Clean up previous packages
rm -rf build dist replacement.egg-info

# Create package
python3 setup.py sdist bdist_wheel
