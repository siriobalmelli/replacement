'''setup.py
PyPI build for replacement package
(c) 2018 Anthony Soenen and Sirio Balmelli
'''
from setuptools import setup, find_packages
from replacement import name, version

with open("README.md", "r") as fh:
    LONG = fh.read()

setup(
    name=name,
    version=version,
    packages=find_packages(),

    install_requires=['ruamel.yaml'],
    python_requires='>=3.5',

    entry_points={'console_scripts': ['replacement = replacement:main']},

    author="Sirio Balmelli",
    author_email="sirio.bm@gmail.com",
    description="Replacement is a python utility that parses a yaml template and outputs text.",
    license='Apache',
    keywords='replacement template substitute compile',
    url="https://github.com/siriobalmelli/replacement",
    long_description=LONG,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)
