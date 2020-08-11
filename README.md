# Replacement [![Build Status](https://travis-ci.org/siriobalmelli/replacement.svg?branch=master)](https://travis-ci.org/siriobalmelli/replacement)

Replacement is a python utility that parses a yaml template and outputs text.

## Installing

`pip3 install replacement`

or, if you use [nix](https://nixos.org/):

`nix-env --install -A 'nixpkgs.python3Packages.replacement'`

## Introduction

NOTE: the examples given here are further documented in the
  [tests](replacement/tests/README.md).

A `template` is a YAML file containing a `replacement` object.

A replacement object contains a list of `blocks`.

### 1. basic template

A template:

```yaml
---
# simplistic template example
# tests/hello.yaml
replacement:
  - text: text
    input:
      hello world
...
```

Execute a template using `replacement`:

```bash
$ replacement -t tests/hello.yaml
hello world
```

Blocks always begin with a `directive`, which specifies:
  - the data type the block will `yield`, such as `text` or a `dict`
  - the input data type, such as `file` or `yaml`

In the block above, `text: text` is the directive;
  it specifies the block takes `text` input and yields `text` output.

### 2. reading from a file

File `hello.out`:

```
hello world
```

```yaml
---
# read from file
# tests/file.yaml
replacement:
  - text: file
    input:
      hello.out
...
```

```bash
$ replacement -t tests/file.yaml
hello world
```

Notice that:

- The directive in the above block is `text: file`;
  this means: "yield text, input from a file".
- The `input` key is used for the filename to be read;
  in the first example `input` was used to store the literal text input.
- File paths are relative to the path of the template.

### intermission: schema

A schema of all the replacement directives is contained in [schema.yaml](./schema.yaml).

Here is a snippet showing just the `directive` and `input` portions of a block:

```yaml
---
##
# format of a block
##
block:
  - yield: inputType  # this is a directive
    input: inputVal

##
# definition of schema elements
##
schema:
  # 'yield' : what to output (how to format output)
  yield:
    - text  # text: a list of newline-separated strings
    - dict  # a dictionary of key-value pairs
    - meta  # output nothing: set a metadata (substitution dictionary) variable

  # 'input' : where to source data
  inputType:
    # we can input everything we output (see 'yield' above)
    - text
    - dict
    - meta  # a key-value pair retrieved from substitutions dictionary
    # we can also input from other sources
    - file  # open a file on disk
    - eval  # python3 eval() statement
    - func  # import and then call call a function
    - exec  # subprocess execution (usually bash)

  inputVal: input_specific
...
```

### 3. metadata and substitution

The `meta` directive specifies that the output of a block should be inserted
    into the "substitutions dictionary" (aka: `meta`).

- this implies input must be a valid dictionary
- replacement will parse YAML or JSON (which is a subset of YAML)

The `proc` keyword specifies that block output should be processed
    (string substitution).
Valid `proc` directives are:

- `format` :: `str.format()`
- `substitute` :: `string.Template().substitute()`
- `safe_substitute` :: `string.Template().safe_substitute()`

```yaml
---
# metadata
# tests/metadata.yaml
replacement:
  # parse 'input' and insert the resulting dictionary into 'meta'
  - meta: dict
    # metadata may be given as an object
    input:
      version: 1.1
      tag: my_awesome_tag
  - meta: text
    # metadata may be given as text which can be parsed as valid YAML
    input: |
      ---
      message: hello world
      ...
  - meta: text
    # metadata may also be given as JSON
    input: |
      { "hi": 5 }
  # use 'proc' to specify that 'str.format(**meta)' should be run on output
  - text: text
    proc: format
    input: |
      v{version} tag "{tag}"
  - text: text
    proc: substitute
    input: |
      message $message
  - text: text
    proc: safe_substitute
    input: |
      hi $hi
      this value may not exist - $nonexistent
...
```

```bash
$ replacement -t tests/metadata.yaml
v1.1 tag "my_awesome_tag"
message hello world
hi 5
this value may not exist - $nonexistent
```

Metadata can also be read from a file.

File `a.json`:

```json
{
"hello": "world",
"hi": 5,
"list": [ 1, 2, 3, 4 ]
}
```

```yaml
---
# metadata
# tests/meta_file.yaml
replacement:
  # parse file, inserting result into metadata dictionary
  - meta: file
    input:
      a.json
      # string substitution with 'proc'
  - text: text
    proc: format
    input: |
      hello {hello}
      hi {hi}
      list {list}
...
```

```bash
$ replacement -t tests/meta_file.yaml
hello world
hi 5
list [1, 2, 3, 4]
```

### 3a. value -> dictionary using `key`

```yaml
---
# insert contents of file as metadata
# tests/file_as_meta.yaml
replacement:
  - text: dict
    input:
      # produces {"hello": "hi"}
      - dict: text
        key: hello
        input: |
          hi
      - dict: file
        key: contents
        input: hello.out

      - meta: file
        key: data
        input: prep.out
      - dict: dict
        prep: substitute
        input:
          also: $data

      - meta: file
        key: largefile
        input: recurse.out

      - dict: dict
        prep: format
        input:
          hello: world
          hi: |
            {largefile}
...
```

```bash
---
hello: hi
contents: hello world
also: hello world
hi: |-
  recursed inline
  v1.1 tag "my_awesome_tag"
  message hello world
  hi 5
  this value may not exist - I exist I promise!
...
```

### 4. nesting

1. Blocks are executed in sequence, and may nest.
    - nested blocks may extend/alter `meta`, which will be seen by
      later blocks or child blocks, but **not** parent blocks.

```yaml
---
# nesting and dictionaries
# tests/nesting.yaml
replacement:
  # parse 'input' and insert the resulting dictionary into 'meta'
  - meta: dict
    input:
      version: 1.1
  # same thing, but parse *text* input, instead of a dictionary
  - meta: text
    input: |  # note the '|'
      ---
      tag: my_awesome_tag
      ...
  # use 'proc' to specify that 'str.format(**meta)' should be run on output
  - text: text
    proc: format
    input: |
      v{version} tag "{tag}"
  - text: text
    input:
      # metadata additions/changes seen by later blocks and any children,
      # but seen outside this list
      - meta: dict
        input:
          version: 1.0
      - text: text
        proc: format
        input: |
          #v{version} tag "{tag}" (version clobbered in inner scope)
      - text: file
        input:
          hello.out  # contains 'hello world'
  - text: text
    proc: format
    input: |
      outer still v{version}
...
```

```bash
$ replacement -t tests/nesting.yaml
v1.1 tag "my_awesome_tag"
#v1.0 tag "my_awesome_tag" (version clobbered in inner scope)
hello world
outer still v1.1
```

### 5. preprocessing

Substitution can also be performed on the values of the block itself
*before* it is parsed.
The keyword `prep` is used, with the same semantics as `proc` (above):

```yaml
---
# preprocessing
# tests/prep.yaml
replacement:
  - meta: dict
    input:
      filename: hello.out
  # preprocessing will substitute {filename} before evaluating 'file' input
  - text: file
    prep: format
    input: |
      {filename}
...
```

```bash
$ replacement -t tests/prep.yaml
hello world
```

### 6. access to python `eval`

```yaml
---
# use of eval
# tests/an_eval.yaml
replacement:
  # 'eval' returning a dictionary that can me appended to 'meta'
  - meta: eval
    input: |
      {"hello": 5 + 1}
  - text: text
    prep: format
    input: |
      hello {hello}
  # eval returning a scalar value
  - text: eval
    prep: format
    input: |
      {hello}**3
...
```

```bash
$ replacement -t tests/an_eval.yaml
hello 6
216
```

### 7. python `exec`

Sometimes it is advantageous to manipulate the runtime environment.

In the below example, this is being used to import a module which will
be needed by a subsequency call to `eval`.

```yaml
---
# use of eval with an exec statement to execute an import call
# tests/eval_exec.yaml
replacement:
  - meta: exec
    input: |
      global IPv4Network
      from ipaddress import IPv4Network
  - meta: eval
    input: |
      {'gateway': str([h for h in IPv4Network('192.168.1.0/24').hosts()][-1])}
  - text: text
    prep: format
    input: |
      my gateway is {gateway}
...
```

```bash
$ replacement -t tests/eval_exec.yaml
my gateway is 192.168.1.254
```

NOTE: python `exec` is very powerful,
please *avoid* running `replacement` as a privileged user.

### 8. imports and function execution

The `func` input directive can be used to find and call an external function
(see [demo.py](tests/demo.py) for reference):

```yaml
---
# function execution
# tests/func.yaml
replacement:
  # run a function returning a dictionary, and merge that into 'meta'
  - meta: func
    args:
      existing: {'original': 'thesis'}
    # NOTE that this is sensitive to PYTHONPATH
    input: |
      ret_a_dict ./demo.py
  - text: text
    prep: format
    input: |
      original {original}
      secret {secret}

  # run a function returning a dictionary and export return as JSON
  - text: func
    options:
      - json  # emit JSON rather than YAML (the default)
    args:
      existing: {'original': 'thesis'}
    input: |
      ret_a_dict ./demo.py

  # run a function returning an IOStream
  - text: func
    args: {}
    # notice non-portable BRAINDEAD python dot.notation
    # ... will break if 'replacement' (the script) is MOVED vis-a-vis demo.py
    # (of OF COURSE the CWD is blithely ignored ... why would ANYONE use it LOL)
    # TLDR: use the '[symbol] [path]' notation in the preceding example
    input: |
      tests.demo.ret_a_stream

  # A function returning a list of lines of text
  # (using the proper, cleaner import strategy)
  - text: func
    args:
      an_arg: ["question"]
    input: |
      ret_a_list ./demo.py

  # a static function inside a class
  - text: func
    input: |
      aClass.invented_list ./demo.py
```

```bash
$ replacement -t tests/func.yaml
original thesis
secret 42
{"secret": 42, "original": "thesis"}
1. hello
2. world
42
meaning
question
hello
from
staticmethod
```

### 9. Recursion

Or, how I learned to stop worrying and have templates import other templates.

```yaml
---
# recursion (nested 'replacement' templates)
# tests/recurse.yaml
replacement:
  # parse a 'replacement' template inline
  - replacement: text
    input: |
      ---
      replacement:
        - text: text
          input: |
            recursed inline
      ...
  - meta: dict
    input:
      nonexistent: "I exist I promise!"
  # parse a replacement template from a file
  # NOTE *relative* path)
  # NOTE our 'meta' dictionary is propagated to child replacement being parsed
  - replacement: file
    input: metadata.yaml
...
```

```bash
$ replacement -t tests/recurse.yaml
recursed inline
v1.1 tag "my_awesome_tag"
message hello world
hi 5
this value may not exist - I exist I promise!
```

## Development

The recommended development environment is:

1. Python `venv` with `nix`:

        nix-shell --pure  # activates a venv

    alternately:

        python -m venv venv
        venv/bin/activate
        alias pip="python -m pip"

1. Install requirements:

        pip install -r requirements.txt
        pip install -e .

1. Test and build:

        pytest
        ./create_package.sh

## NOTES

1. This documentation is itself built as a template, so that the content
of `.yaml` tests and `.out` results is kept in sync with the [tests](./tests)
directory.
See [README.template.yaml](./README.template.yaml) and [gen_readme.sh](./gen_readme.sh).

## Project TODO

Project TODO list

1. subprocess execution and output capture

1. accept template from STDIN, not just a template file

1. Packaging:
    - proper test runner (perhaps [tox](https://tox.readthedocs.io/en/latest/)?)
    - add test runner to all the builds

1. Dependency output command: runs all preprocessing and outputs a list of
  file dependencies.
For use e.g. in Makefiles.

1. Express [the schema](replacement/schema.yaml) formally and write validation code for it.
