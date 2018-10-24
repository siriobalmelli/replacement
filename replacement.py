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


def lin_sub(lin=[], meta={}, method='literal'):  # pylint: disable=dangerous-default-value
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
        inputs = {'text': lambda: [lin for lin in inp.split(meta['eol'])],
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
    do_yield, do_input = [(yld, inp)
                          for yld, inp in blk.items()
                          if yld in yields and inp in inputs][0]
    assert do_yield and do_input, 'broken yield statement'  # TODO: debug printing
    do_yield = yields[do_yield]
    do_input = inputs[do_input]

    return do_yield(do_input())


def replacement(path={}, meta={}):  # pylint: disable=dangerous-default-value
    '''replacement()
    path    :   path to the YAML template
                to be opened and processed
    meta    :   optional dictionary of key:value pairs
                to be used in processing 'path'
    '''
    # template file
    with open(path, 'r') as fil:
        template = ruamel.yaml.load(fil, Loader=ruamel.yaml.Loader)
    # TODO: proper error printing
    assert 'replacement' in template, 'no "replacement" object in ' + path
    template = template['replacement']

    # paths are relative to template: chdir to template dir
    chd = os.path.dirname(path)
    if chd:
        cwd = os.getcwd()
        os.chdir(chd)

    # sane default for line endings
    if 'eol' not in meta:
        meta['eol'] = '\n'

    out, meta = [line for block in template for line in do_block(block, meta)]

    if chd:
        os.chdir(cwd)
    return meta['eol'].join(out)


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

    print(replacement(args.yaml, meta))

#   main
if __name__ == "__main__":
    main()
