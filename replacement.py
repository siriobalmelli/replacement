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


def dic_sub(dic={}, meta={}, method='format'):  # pylint: disable=dangerous-default-value
    '''dic_sub()
    Substitute all string values in 'dic' against 'meta' dictionary using 'method'.
    Does NOT recurse.
    '''
    methods = {'format': lambda stg, dic: stg.format(**dic),
               'substitute': lambda stg, dic: string.Template(stg).substitute(**dic),
               'safe_substitute' : lambda stg, dic: string.Template(stg).safe_substitute(**dic)
              }
    sub = methods.get(method)
    if not sub:
        return dic
    return {k: sub(v, meta) if isinstance(v, str) else v
            for k, v in dic}


def dic_merge(in_to, *out_of):
    ''''dic_merge()
    Copy 'in_to'; merge each dictionary in 'out_of' into this copy and return it.
    '''
    # TODO: implement
    return in_to


def lin_sub(lin=[], meta={'eol': '\n'}, method='literal'):  # pylint: disable=dangerous-default-value
    '''lin_sub()
    Clean up or substitute each text line according to 'method'.
    NOTE: 'meta' must contain an "eol" entry.
    '''
    methods = {'literal': lambda stg, dic: stg,
               'format': lambda stg, dic: stg.format(**dic),
               'substitute': lambda stg, dic: string.Template(stg).substitute(**dic),
               'safe_substitute' : lambda stg, dic: string.Template(stg).safe_substitute(**dic)
              }
    sub = methods.get(method) or methods.get('literal')
    return [sub(lin, meta).rstrip(meta['eol']) for lin in lin]


def get_file(path):
    '''get_file()
    Return lines in file at 'path' as a list of lines.
    '''
    with open(path, 'r') as fil:
        return [lin for lin in fil]


def do_block(blk={}, meta={}):  # pylint: disable=dangerous-default-value
    ''''do_block()
    Process a block.
    Recursive.
    Returns ('out', 'meta').
    '''
    yields = {'text': lambda output: (lin_sub(output, meta, blk.get('proc')),
                                      meta),
              'dict': lambda output: (dic_sub(output, meta, blk.get('proc')),
                                      meta),
              'meta': lambda output: (None,
                                      dic_merge(dic_sub(output, meta, blk.get('proc')),
                                                meta))
             }

    inp = blk['input']  # it is a hard fault not to have 'input'
    if isinstance(inp, str):
        inputs = {'text': lambda: [lin for lin in inp.split(meta['eof'])],
                  'dict': None,
                  'meta': None,
                  'file': lambda: get_file(inp),
                  'eval': None,
                  'function': None,
                  'exec': None
                 }
    elif isinstance(inp, list):
        inputs = {'text': None,
                  'dict': None,
                  'meta': None,
                  'file': None,
                  'eval': None,
                  'function': None,
                  'exec': None
                 }
    else:
        assert False, 'input type ' + type(inp) + ' invalid'

    # get 'yield: input' function pair
    do_yield, do_input = [(name, blk[name])
                          for name in blk.keys()
                          if name in yields and blk[name] in inputs][0:1]
    assert do_yield and do_input, 'broken yield statement'  # TODO: debug printing
    do_yield = yields[do_yield]
    do_input = inputs[do_input]

    return do_yield(do_input())

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
