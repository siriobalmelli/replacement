from importlib import import_module
from glob import glob
from os import path
from sh import replacement
import pytest


def test_basic_import():
    import_module('replacement')


prefix = path.dirname(__file__)
yaml_files = glob(f'{prefix}/*.yaml')


@pytest.mark.parametrize('testfile', yaml_files)
def test_yaml_file(testfile):
    out = replacement('-t', testfile)
    comp = open(testfile.replace('.yaml', '.out')).read()
    if out != comp:
        raise RuntimeError((f'expected:\n'
                            f'{comp}\n\n'
                            f'{testfile} yielded:\n'
                            f'{out}'))
