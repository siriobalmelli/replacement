#!/usr/bin/env python3
''''replacement.py
python3 templating tool.
(c) 2018 Sirio Balmelli
'''
name = "replacement"

import importlib
import os
import sys
import json
import string
from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO


# A shiny global ruamel.yaml obj with sane options (dumps should pass yamllint)
YM = YAML()
YM.indent(mapping=2, sequence=4, offset=2)
YM.explicit_start = True
YM.explicit_end = True
YM.allow_unicode = True
YM.preserve_quotes = True


# global line separator
EOL = '\n'


##
#   substitution
##
def subst_dict(dic, meta, method):  # pylint: disable=dangerous-default-value
    '''subst_dict()
    String-coerce all string-able values in 'dic', optionally substitute them
    against 'meta' using 'method'.
    Does NOT recurse into sub-objects or lists.
    '''
    dic = dic or {}
    methods = {'literal': str,  # assume only passthrough *needs* string coercion
               'format': lambda stg: stg.format(**meta),
               'substitute': lambda stg: string.Template(stg).substitute(**meta),
               'safe_substitute' : lambda stg: string.Template(stg).safe_substitute(**meta)
              }
    sub = methods.get(method) or methods.get('literal')
    return {k: (sub(v).rstrip(EOL) if isinstance(v, (str, float, int)) else v)
            for k, v in dic.items()}

def subst_line(lin, meta, method):
    '''subst_line()
    Clean up or substitute each text line according to 'method'.
    '''
    lin = lin or []
    methods = {'literal': str,  # passthrough case does string coercion
               'format': lambda stg: stg.format(**meta),
               'substitute': lambda stg: string.Template(stg).substitute(**meta),
               'safe_substitute' : lambda stg: string.Template(stg).safe_substitute(**meta)
              }
    sub = methods.get(method) or methods.get('literal')
    return [sub(lin).rstrip(EOL) for lin in lin]


##
#   merging
##
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


##
#   get/find/execute
##
def get_file(path):
    '''get_file()
    Return lines in file at 'path' as a list of lines.
    '''
    with open(path, 'r') as fil:
        return [lin for lin in fil]

def get_import(name):
    '''get_import()
    Look for 'name' function in existing namespaces; try to import it if not found
    '''
    # Function in existing namespaces must match EXACTLY else it may belong to another module
    func = locals().get(name) or globals().get(name)
    if func:
        return func

    # Try to import, starting from leftmost token and ignoring rightmost
    #+  e.g.: for 'toaster.ToasterClass.sanitize', try:
    #+      -> path: toaster                name: ToasterClass.sanitize
    #+      -> path: toaster.ToasterClass   name: sanitize
    lst = name.split('.')
    for path, tok in [('.'.join(lst[:-i]), '.'.join(lst[-i:]))
                      for i in range(1, len(lst)).__reversed__()]:
        try:
            mod = importlib.import_module(path)
            for item in tok.split('.'):
                mod = getattr(mod, item)
            return mod
        except:  # pylint: disable=bare-except
            pass

    print('could not find/import function: ' + name, file=sys.stderr)
    print('NOTE that this is sensitive to PYTHONPATH', file=sys.stderr)
    return None


##
#   transformation
##
def listify(alors):
    '''listify()
    'alors' is us assuming "a list (of strings) or string" as input
    '''
    if isinstance(alors, list):
        return alors
    return [lin for lin in alors.strip(EOL).split(EOL)]

def stringify(unk, as_json=False):
    '''stringify()
    'unk' may be:
    - already a string
    - list of string lines (possibly empty)
    - a dictionary object (must be rendered as YAML/JSON)
    - already a string (leave alone)
    - another scalar (int, float, etc) which should be stringified
    '''
    if isinstance(unk, str):
        return unk
    # lists are flattened only if they are empty or are lists of strings
    if isinstance(unk, list) and (not unk or isinstance(unk[0], str)):
        return EOL.join(unk)
    # dictionaries are dumped to YAML or, if requested, JSON
    if isinstance(unk, dict):
        if as_json:
            return json.dumps(unk)
        stream = StringIO()
        YM.dump(unk, stream)
        return stream.getvalue()
    # scalars returned stringified
    return str(unk)

def dictify(unk):
    '''dictify()
    'unk' is "unknown"
    '''
    # dictionary is pass-through
    if isinstance(unk, dict):
        return unk
    # otherwise should be valid YAML (JSON is a subset of YAML)
    unk = stringify(unk)
    try:
        return YM.load(unk)
    except:  # pylint: disable=bare-except
        print('cannot parse supposed dictionary: ' + unk, file=sys.stderr)
        return {}


##
#   template execution (aka: 'replacement' itself)
##
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

    inp = blk['input']  # it is a hard fault not to have 'input' in block

    # 'im' is "intermediate", denoting a value which may be:
    # 1. a string
    # 2. a list of strings
    # 3. either of those, but containing:
    #   - a YAML string
    #   - a JSON string
    # 4. a dictionary object directly encoded in the YAML
    # NOTE: it is arguable *more* efficient to have these *inside* the function
    # instead of as globals, as it obviates a large amount of variable passing
    yields = {'text': lambda im: (subst_line(listify(im), meta, blk.get('proc')),
                                  meta),
              'dict': lambda im: (subst_dict(dictify(im), meta, blk.get('proc')),
                                  meta),
              'meta': lambda im: (None,
                                  # merge 'meta' into self (clobber meta)
                                  merge_dict(subst_dict(dictify(im), meta, blk.get('proc')),
                                             meta))
             }

    if isinstance(inp, list):
        inz = {'text': lambda: do_recurse(inp, meta, merge_line),
               'dict': lambda: do_recurse(inp, meta, merge_dict)
              }
    else:  # relies on string coercion in "preprocess" above
        is_js = 'json' in blk.get('options', [])  # whether to stringify objects as JSON or YAML
        inz = {'text': lambda: inp,
               'dict': lambda: stringify(inp, is_js),
               'meta': lambda: inp,
               'file': lambda: get_file(inp),
               'eval': lambda: stringify(eval(inp)),  # pylint: disable=eval-used
               'func': lambda: stringify(get_import(inp)(**blk.get('args', {})), is_js),
               'exec': None  # TODO
              }

    # get 'yield: input' function pair
    do_yield, do_input = [(yld, inp)
                          for yld, inp in blk.items()
                          if yld in yields and inp in inz][0]
    assert do_yield and do_input, 'no valid "yield" statement found'
    do_yield = yields[do_yield]
    do_input = inz[do_input]
    return do_yield(do_input())


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
        try:
            data, meta = do_block(blk, meta)
        except Exception as exc:
            print('# ------------- error --------------------', file=sys.stderr)
            print('# trace: block', file=sys.stderr)
            YM.dump(blk, sys.stderr)
            print('# trace: meta', file=sys.stderr)
            print('', file=sys.stderr)
            YM.dump(meta, sys.stderr)
            print('# ----------------------------------------', file=sys.stderr)
            raise exc
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
        template = YM.load(fil)
    assert 'replacement' in template, 'no "replacement" object in ' + path
    template = template['replacement']

    # paths are relative to template: chdir to template dir
    chd = os.path.dirname(path)
    if chd:
        cwd = os.getcwd()
        os.chdir(chd)

    # allow caller to set alternate line endings
    meta = meta or {}
    if 'eol' in meta:
        global EOL  # pylint: disable=global-statement
        EOL = meta['eol']

    out = [line for line in do_recurse(template, meta)]

    if chd:
        os.chdir(cwd)
    return EOL.join(out)


def main():
    '''main()
    '''
    import argparse

    # args
    desc = '''replacement: the YAML templating utility.'''
    parser = argparse.ArgumentParser(description=desc,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-t', '--template', metavar='YAML_PATH', dest='yaml', type=str,
                        help='''Execute 'replacement' directive in this YAML template.''')
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                        help='''Print metadata (substitutions dictionary) to stderr.''')
    parser.add_argument(metavar='META', dest='meta', nargs='*',
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

    if not args.yaml:
        print('''we require a template path; use '-t YAML_PATH' flag.\n\n''', file=sys.stderr)
        parser.print_help()
        exit(1)

    print(replacement(args.yaml, meta))

#   main
if __name__ == "__main__":
    main()
