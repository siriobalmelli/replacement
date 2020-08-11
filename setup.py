"""setup.py
PyPI build for replacement package
(c) 2020 Anthony Soenen and Sirio Balmelli
"""
from os import path
from replacement import __version__, __description__
from setuptools import setup, find_packages

with open(path.join(path.dirname(__file__), 'README.md')) as readme:
    LONG_DESCRIPTION = readme.read()

setup(
    name='replacement',
    version=__version__,
    description=__description__,

    use_scm_version=True,

    python_requires='>=3.6',  # f-strings
    install_requires=[
        'ruamel.yaml>=0.16.0'  # reproducible YAML representation
    ],
    extras_require={
        'dev': ['pytest']
    },

    packages=find_packages(),
    entry_points={'console_scripts': ['replacement = replacement:main']},

    author='Sirio Balmelli',
    author_email='sirio.bm@gmail.com',
    license='Apache',
    keywords='replacement template substitute compile',
    url='https://github.com/siriobalmelli/replacement',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
    ],
)
