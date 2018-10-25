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


def subst_dict(dic, meta, method):  # pylint: disable=dangerous-default-value
    '''subst_dict()
    String-coerce all string-able values in 'dic', optionally substitute them
    against 'meta' using 'method'.
    Does NOT recurse into sub-objects or lists.
    '''
    dic = dic or {}
    methods = {'literal': lambda stg, dic: stg,
               'format': lambda stg, dic: stg.format(**dic),
               'substitute': lambda stg, dic: string.Template(stg).substitute(**dic),
               'safe_substitute' : lambda stg, dic: string.Template(stg).safe_substitute(**dic)
              }
    sub = methods.get(method) or methods.get('literal')
    return {k: sub(str(v), meta) if isinstance(v, (str, float, int)) else v
            for k, v in dic.items()}

def subst_line(lin, meta, method):
    '''subst_line()
    Clean up or substitute each text line according to 'method'.
    NOTE: 'meta' must contain an "eol" entry.
    '''
    lin = lin or []
    methods = {'literal': lambda stg, dic: stg,
               'format': lambda stg, dic: stg.format(**dic),
               'substitute': lambda stg, dic: string.Template(stg).substitute(**dic),
               'safe_substitute' : lambda stg, dic: string.Template(stg).safe_substitute(**dic)
              }
    sub = methods.get(method) or methods.get('literal')
    return [sub(lin, meta).rstrip(meta['eol']) for lin in lin]


def merge_dict(in_to, *out_of):
    ''''merge_dict()
    Merge each dictionary in 'out_of' into 'in_to' and return it.
    '''
    in_to = in_to or {}
    for obj in out_of:
        def scalar(thing=None):
            return thing is None or isinstance(thing, str) or not hasattr(thing, "__len__")

        # expose a uniform way of inserting into 'a'
        # ... depend on exceptions in case these don't pan out against b's datatype
        # (putting the "duck" and "cower" firmly into duck-typing).
        if hasattr(in_to, "update"):
            def push(key, val=None):
                '''push()
                Check (and if kosher, push) key:val into 'in_to' - 'in_to' being a dictionary
                '''
                # new keys inserted as-is
                if key not in in_to:
                    in_to[key] = val
                    return
                # duplicate values ignored
                if in_to[key] == val:
                    return
                # otherwise, merge recursively
                # NOTE that 2 conflicting scalars will become a list
                merge_dict(in_to[key], val)

        else:
            # 'in_to' must be "insertable-into-able"
            if not hasattr(in_to, "append"):
                in_to = [in_to]
            def push(key, val=None):
                '''push_list()
                Push into 'in_to' as in_to list.
                '''
                if val:
                    key = {key: val}
                in_to.append(key)

        # dictionary (key: value) types have an "items" function
        if hasattr(obj, "items"):
            for key, val in obj.items():
                push(key, val)
        # other iterable types are, well, iterable :P
        elif hasattr(obj, "__iter__"):
            for val in obj:
                push(val)
        # scalar?
        elif scalar(obj):
            push(obj)
        # garbage!
        else:
            raise Exception("cannot merge type '{0}'".format(type(obj)))
    return in_to

def merge_line(in_to, *out_of):
    '''merge_line()
    Concatenate multiple lists
    '''
    return (in_to or []) + [lin for lst in out_of for lin in lst]


def get_file(path):
    '''get_file()
    Return lines in file at 'path' as a list of lines.
    '''
    with open(path, 'r') as fil:
        return [lin for lin in fil]


def do_block(blk, meta):
    ''''do_block()
    Process a block.
    Recursive.
    Returns ('out', 'meta').
    '''
    blk = blk or {}

    # Preprocess block before parsing it.
    # Will string-coerce scalars in the block whether a 'prep' directive
    # was given or not.
    blk = subst_dict(blk, meta, blk.get('prep'))

    eol = meta['eol']  # it is a hard fault not to have 'eol' in meta

    # transforms
    # NOTE: "alors" is "a list or string"
    def listify(alors):
        '''listify()
        '''
        if isinstance(alors, list):
            return alors
        return [lin for lin in alors.strip(eol).split(eol)]
    def flatten(alors):
        '''flatten()
        '''
        if isinstance(alors, list):
            alors = eol.join(alors)
        return alors
    def dictify(unk):
        '''dictify()
        '''
        # dictionary is pass-through
        if isinstance(unk, dict):
            return unk
        unk = flatten(unk)
        # attempt to parse as JSON or YAML (good old "program by exception")
        try:
            return json.loads(unk)
        except:  # pylint: disable=bare-except
            pass
        try:
            return ruamel.yaml.load(unk, Loader=ruamel.yaml.Loader)
        except:  # pylint: disable=bare-except
            pass
        # last-resort: return as-is
        return unk

    # 'im' is "intermediate", denoting a string which may or may not
    yields = {'text': lambda im: (subst_line(listify(im), meta, blk.get('proc')),
                                  meta),
              'dict': lambda im: (subst_dict(dictify(im), meta, blk.get('proc')),
                                  meta),
              'meta': lambda im: (None,
                                  # merge into 'meta' at 'spec' key (clobber meta)
                                  merge_dict(subst_dict({blk['spec']: dictify(im)},
                                                        meta,
                                                        blk.get('proc')),
                                             meta))
             }

    inp = blk['input']  # it is a hard fault not to have 'input' in block
    if isinstance(inp, list):
        inputs = {'text': lambda: do_recurse(inp, meta, merge_line),
                  'dict': lambda: do_recurse(inp, meta, merge_dict)
                 }
    else:  # relies on string coercion in "preprocess" above
        inputs = {'text': lambda: inp,
                  'dict': lambda: inp,
                  'meta': None,
                  'file': lambda: get_file(inp),
                  'eval': lambda: eval(inp),  # pylint: disable=eval-used
                  'function': None,
                  'exec': None
                 }

    # get 'yield: input' function pair
    do_yield, do_input = [(yld, inp)
                          for yld, inp in blk.items()
                          if yld in yields and inp in inputs][0]
    assert do_yield and do_input, 'broken yield statement'  # TODO: debug printing
    do_yield = yields[do_yield]
    do_input = inputs[do_input]

    #print('--- do_block: ---')
    #print(blk)
    #print(meta)
    #print(inp)
    ret = do_yield(do_input())
    #print(ret)
    #print('-----------------')
    return ret

def do_recurse(blk_list=[], meta={}, merge_func=merge_line):  # pylint: disable=dangerous-default-value
    '''do_recurse()
    Recursively execute a series of blocks:
    - merging the output of each into the output of the previous
    - propagating any changes to 'meta' through to successive blocks

    NOTE that we do not, ourselves, return a (potentially modified) 'meta'.
    NOTE that merge_func() MUST be able to accept a None input.
    '''
    out = None
    for blk in blk_list:
        data, meta = do_block(blk, meta)
        if data:  # may have been a 'meta' block returning no data
            out = merge_func(out, data)
    return out


def replacement(path, meta):
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
    meta = meta or {}
    if 'eol' not in meta:
        meta['eol'] = '\n'

    out = [line for line in do_recurse(template, meta)]

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
