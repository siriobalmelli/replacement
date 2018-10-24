#!/usr/bin/env python3
''''replacement.py

python3 templating tool.
(c) 2018 Sirio Balmelli
'''

import json
import importlib
import os
import string
import ruamel.yaml


class Replacement():
    '''Replacement
    A Replacement instance is comprised of:
        - the 'replacement' object: the template
        - the 'meta' dictionary: string substitutions, general variables
    '''
    tpl = {}  # type: dict
    meta = {  # substitutions dictionary, containing sane formatting defaults
        'eol': '\n'
    }
    out = []  # type: list


    def __init__(self, templatePath, metadata={}):  # pylint: disable=dangerous-default-value
        '''__init__()

        templateFile    :   path to the YAML template
                            to be opened and processed
        meta            :   optional dictionary of key:value pairs
                            to be used in processing 'templateFile'
        '''
        self.meta.update(metadata)

        # template file
        with open(templatePath, 'r') as fil:
            dic = ruamel.yaml.load(fil, Loader=ruamel.yaml.Loader)
        # TODO: proper error printing
        assert 'replacement' in dic, 'no "replacement" object in ' + templatePath
        self.tpl = dic['replacement']

        # paths are relative to template: chdir to template dir
        chd = os.path.dirname(templatePath)
        if chd:
            cwd = os.getcwd()
            os.chdir(chd)

        self.out = [line
                    for block in self.tpl
                    for line in self.block(block)]

        if chd:
            os.chdir(cwd)


    def render(self):
        '''render()
        return the rendered template as a list of lines
        '''
        return self.meta['eol'].join(self.out)

    def block(self, block={}):  # pylint: disable=dangerous-default-value
        '''block()
        Recursively parse/execute 'block';
        yield/return type is dictated by the block itself.

        NOTE: refers to (and potentially alters) self.meta
        '''
        eol = self.meta['eol']  # legibility

        # TODO: preprocess

        # parse directive e.g. 'text: file'
        out = [(v, block[k]) for k, v in {'text': list, 'dict': dict, 'meta': None}.items()
               if k in block]
        # TODO: proper error printing
        assert len(out) == 1, '''exactly one 'yield' directive per block'''
        sink, source = out[0]

        # TODO: input
        if source == 'text':
            source = block['input'].split(eol)
        elif source == 'file':
            with open(block['input'], 'r') as fil:
                source = [lin.strip(eol) for lin in fil]

        # TODO: yield
        if sink is list and isinstance(source, list):
            return source

        # TODO: postprocess
        return []


def main():
    '''main()
    '''
    import argparse

    # args
    desc = '''replacement: the YAML templating utility.'''
    parser = argparse.ArgumentParser(description=desc,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-t', '--template', metavar="YAML", dest='yaml', type=str,
                        help='''Execute 'replacement' directive in this YAML template.''')
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                        help='''Print metadata (substitutions dictionary) to stderr.''')
    parser.add_argument(metavar="META", dest='meta', nargs='*',
                        help='''
A "key:value" pair.
Key-value pairs are added to the substitutions dictionary
    used in executing YAML.
NOTE: separation into key:value is done at the first ':' ONLY;
    "a:b:c" becomes "a" : "b:c"
                        ''')
    args = parser.parse_args()

    # parse any tokens
    # we split on the first ':' ... values can contain ':' characters
    meta = {k:v for k, v in (tok.split(':', 1) for tok in args.meta if tok)
            if k and v}

    assert not args.verbose, 'verbose not implemented'

    rep = Replacement(args.yaml, meta)
    print(rep.render())

#   main
if __name__ == "__main__":
    main()
