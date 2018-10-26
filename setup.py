# Setup.py
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="replacement",
    version="0.1.0",
    author="Sirio Balmelli",
    author_email="sirio@b-ad.ch",
    description="Replacement is a python utility that parses a yaml template and outputs text.",
	license='Apache',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/siriobalmelli/replacement",
    packages=setuptools.find_packages(),
	install_requires=[ 'ruamel.yaml' ], 
	python_requires='>=3',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)
