#!/usr/bin/env python3
''''replacement.py
python3 templating tool.
(c) 2018 Sirio Balmelli
'''
from importlib import import_module
from importlib.util import spec_from_file_location
from importlib.util import module_from_spec
import os
import sys
import json
import string
from io import StringIO, IOBase
from ruamel.yaml import YAML


name = "replacement"  # pylint: disable=invalid-name
version = "0.3.2"  # pylint: disable=invalid-name


# A shiny global ruamel.yaml obj with sane options (dumps should pass yamllint)
YM = YAML()
YM.indent(mapping=2, sequence=4, offset=2)
YM.explicit_start = True
YM.explicit_end = True
YM.allow_unicode = True
YM.preserve_quotes = True


# global formatting (any changes *should* propagate to later directives)
EOL = '\n'  # line separator
RENDER_JS = False


##
#   substitution
##
def subst_stream(strm, meta, method):
    '''subst_stream()
    substitute strings in strm
    return (the same? or a new) stream with substituted values
    '''
    strm = strm or StringIO()
    methods = {'passthrough': lambda stg: stg,
               'format': lambda stg: stg.format(**meta),
               'substitute': lambda stg: string.Template(stg).substitute(**meta),
               'safe_substitute' : lambda stg: string.Template(stg).safe_substitute(**meta)
              }
    sub = methods.get(method) or methods.get('passthrough')
    out = StringIO()
    strm.seek(0)
    out.writelines([sub(lin) for lin in strm])
    return out

def subst_dict(dic, meta, method):
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


##
#   merging
##
def merge_stream(in_to, *out_of):
    '''merge_stream()
    Merge (more like "append") all 'out_out' streams into 'in_to'.
    Assume that in_to seek position is already at end.
    return in_to.
    '''
    in_to = in_to or StringIO()
    for out in out_of:
        out.seek(0)
        in_to.write(out.read())
    return in_to

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


##
#   get/find/execute
##
def get_import(func_name):
    '''get_import()
    Look for 'func_name' function in existing func_namespaces;
    try to import it if not found
    '''
    # Function in existing func_namespaces must match EXACTLY else it may belong to another module
    func = locals().get(func_name) or globals().get(func_name)
    if func:
        return func

    # log all attempted imports so we can trace failures intelligently
    attempts = []

    # import statement may be one of:
    # 1. 'a.b.c' which is standard python but COMPLETELY braindead for files not in PYTHONPATH
    # 2. 'c a/b.py' which is SANE
    # we must of course support both
    paths = func_name.split(' ')
    if len(paths) == 1:
        # Try to import, starting from leftmost token and ignoring rightmost
        #+  e.g.: for 'toaster.ToasterClass.sanitize', try:
        #+      -> path: toaster                func_name: ToasterClass.sanitize
        #+      -> path: toaster.ToasterClass   func_name: sanitize
        lst = func_name.split('.')
        for path, tok in [('.'.join(lst[:-i]), '.'.join(lst[-i:]))
                          for i in range(1, len(lst)).__reversed__()]:
            attempts += ['import_module("{0}")'.format(path)]
            try:
                mod = import_module(path)
                for item in tok.split('.'):
                    mod = getattr(mod, item)
                return mod
            except:  # pylint: disable=bare-except
                pass

    elif len(paths) == 2:
        paths[1] = os.path.join(os.getcwd(), paths[1])
        attempts += ['spec_from_file_location("{0}", "{1}")'.format(paths[0], paths[1])]
        try:
            spec = spec_from_file_location(paths[0], paths[1])
            mod = module_from_spec(spec)
            spec.loader.exec_module(mod)
            return getattr(mod, paths[0])
        except:  # pylint: disable=bare-except
            pass

    print('IMPORT FAIL:', file=sys.stderr)
    for att in attempts:
        print(att, file=sys.stderr)
    return None


##
#   transformation
##
def stringify(scalar):
    '''stringify()
    return a stringified value with *only* EOL at end of line
    '''
    return str(scalar).rstrip() + EOL

def streamify(unk):
    '''streamify()
    Return a stream (with seek position most likely at end)
    '''
    if isinstance(unk, IOBase):
        return unk
    out = StringIO()
    if isinstance(unk, dict):
        if RENDER_JS:
            json.dump(unk, out)
            out.write(EOL)  # JSON doesn't dump a terminating newline
        else:
            YM.dump(unk, out)
    elif isinstance(unk, list):
        out.writelines([stringify(lin) for lin in unk])
    else:
        out.write(stringify(unk))
    return out

def dictify(unk):
    '''dictify()
    'unk' may be:
    - already a dictionary
    - a string or stream containing YAML/JSON to be parsed
    - garbage to be ignored, and an empty dictionary issued instead
    '''
    # dictionary is pass-through
    if isinstance(unk, dict):
        return unk
    # otherwise should be valid YAML (JSON is a subset of YAML)
    unk = streamify(unk)
    unk.seek(0)
    try:
        unk = YM.load(unk)
        if isinstance(unk, dict):
            return unk
    except:  # pylint: disable=bare-except
        pass
    # in any event, return an empty dictionary
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

    # 'im' is "intermediate", denoting a value of uncertain type
    yields = {'text': lambda im: (subst_stream(streamify(im), meta, blk.get('proc')),
                                  meta),
              'dict': lambda im: (subst_dict(dictify(im), meta, blk.get('proc')),
                                  meta),
              'meta': lambda im: (None,
                                  # merge 'meta' into self (clobber meta)
                                  merge_dict(subst_dict(dictify(im), meta, blk.get('proc')),
                                             meta)),
              'replacement': lambda im: (replacement(im, meta),
                                         meta)
             }

    if isinstance(inp, list):
        inz = {'text': lambda: replacement(inp, meta, merge_stream),
               'dict': lambda: replacement(inp, meta, merge_dict)
              }
    else:  # relies on string coercion in "preprocess" above
        global RENDER_JS  # pylint: disable=global-statement
        RENDER_JS = 'json' in blk.get('options', [])  # how to stringify

        inz = {'dict': lambda: subst_dict(inp, meta, blk.get('prep')),
               'eval': lambda: eval(inp),  # pylint: disable=eval-used
               'exec': lambda: streamify(exec(inp)),  #pylint: disable=exec-used
               'file': lambda: open(inp, 'r'),
               'func': lambda: streamify(get_import(inp)(**subst_dict(blk.get('args', {}), meta, blk.get('prep')))),
               'replacement': lambda: inp,
               'text': lambda: stringify(inp)
              }

    # get 'yield: input' function pair
    do_yield, do_input = [(yld, inp)
                          for yld, inp in blk.items()
                          if yld in yields and inp in inz][0]
    assert do_yield and do_input, 'no valid "yield" statement found'
    do_yield = yields[do_yield]
    do_input = inz[do_input]
    return do_yield(do_input())


def replacement(parse, meta={}, merge_func=merge_stream):  # pylint: disable=dangerous-default-value
    '''replacement()
    Entrance AND recursion point for replacement.

    'parse' may be:
    - a list of directives to be processed
    - a dictionary containing a 'replacement' list of directives to be parsed
    - an IOBase (StringIO or TextIOWrapper) containing a dictionary with
      a 'replacement' list ...
    - a string giving the filename of a YAML/JSON file containing a dictionary
      containing a 'replacement' list ...

    Once we obtain a list, we execute each block sequentially:
    - merging the output of each into the output of the previous
    - propagating any changes to 'meta' through to successive blocks

    NOTE that we do not, ourselves, return a (potentially modified) 'meta'.
    NOTE that merge_func() MUST be able to accept a None input.
    '''
    chd = None
    path = None

    if not isinstance(parse, list):
        try:
            if not isinstance(parse, dict):
                dic = dictify(parse)
                if not dic:
                    with open(parse, 'r') as fil:
                        dic = YM.load(fil)
                    path = parse
                elif hasattr(parse, 'name'):
                    path = parse.name

                # paths are relative to template: we may need to chdir to template dir
                if path:
                    chd = os.path.dirname(path)
                    if chd:
                        cwd = os.getcwd()
                        os.chdir(chd)
            parse = dic.get('replacement', [])
            if 'eol' in meta:
                global EOL  # pylint: disable=global-statement
                EOL = meta['eol']
        except Exception as exc:  # pylint: disable=bare-except
            print('# ------------- error --------------------', file=sys.stderr)
            print('cannot parse the following as a replacement template:', file=sys.stderr)
            print(parse)
            print('# ----------------------------------------', file=sys.stderr)
            raise exc

    # process block list
    out = None
    for blk in parse:
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

    # undo any dir changes as a result of parsing files
    if chd:
        os.chdir(cwd)
    return out or StringIO()


def main():
    '''main()
    '''
    import argparse

    # args
    desc = 'replacement v' + version + ' : the YAML templating utility.'
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
        print('''we require a template path; use '-t YAML_PATH' flag.\n''', file=sys.stderr)
        parser.print_help()
        exit(1)

    sys.stdout.write(replacement(args.yaml, meta).getvalue())
    sys.stdout.flush()

if __name__ == "__main__":
    main()
