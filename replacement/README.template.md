# Replacement [![Build Status](https://travis-ci.org/siriobalmelli/replacement.svg?branch=master)](https://travis-ci.org/siriobalmelli/replacement)

Replacement is a python utility that parses a yaml template and outputs text.

## Installing

`pip3 install replacement`

or, if you use [nix](https://nixos.org/):

`nix-env --install -A 'nixpkgs.python36Packages.replacement'`

## Introduction

NOTE: the examples given here are further documented in the
  [tests](replacement/tests/README.md).

A `template` is a YAML file containing a `replacement` object.

A replacement object contains a list of `blocks`.

### 1. basic template

A template:

```yaml
$hello_yaml
```

Execute a template using `replacement`:

```bash
$ replacement -t tests/hello.yaml
$hello_out
```

Blocks always begin with a `directive`, which specifies:
  - the data type the block will `yield`, such as `text` or a `dict`
  - the input data type, such as `file` or `yaml`

In the block above, `text: text` is the directive;
  it specifies the block takes `text` input and yields `text` output.

### 2. reading from a file

File `hello.out`:

```
$hello_out
```

```yaml
$file_yaml
```

```bash
$ replacement -t tests/file.yaml
$file_out
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
$metadata_yaml
```

```bash
$ replacement -t tests/metadata.yaml
$metadata_out
```

Metadata can also be read from a file.

File `a.json`:

```json
$a_json
```

```yaml
$meta_file_yaml
```

```bash
$ replacement -t tests/meta_file.yaml
$meta_file_out
```

### 3a. value -> dictionary using `key`

```yaml
$file_as_meta_yaml
```

```bash
$file_as_meta_out
```

### 4. nesting

1. Blocks are executed in sequence, and may nest.
    - nested blocks may extend/alter `meta`, which will be seen by
      later blocks or child blocks, but **not** parent blocks.

```yaml
$nesting_yaml
```

```bash
$ replacement -t tests/nesting.yaml
$nesting_out
```

### 5. preprocessing

Substitution can also be performed on the values of the block itself
*before* it is parsed.
The keyword `prep` is used, with the same semantics as `proc` (above):

```yaml
$prep_yaml
```

```bash
$ replacement -t tests/prep.yaml
$prep_out
```

### 6. access to python `eval`

```yaml
$an_eval_yaml
```

```bash
$ replacement -t tests/an_eval.yaml
$an_eval_out
```

### 7. python `exec`

Sometimes it is advantageous to manipulate the runtime environment.

In the below example, this is being used to import a module which will
be needed by a subsequency call to `eval`.

```yaml
$eval_exec_yaml
```

```bash
$ replacement -t tests/eval_exec.yaml
$eval_exec_out
```

NOTE: python `exec` is very powerful,
please *avoid* running `replacement` as a privileged user.

### 8. imports and function execution

The `func` input directive can be used to find and call an external function
(see [demo.py](tests/demo.py) for reference):

```yaml
$func_yaml
```

```bash
$ replacement -t tests/func.yaml
$func_out
```

## 9. Recursion

Or, how I learned to stop worrying and have templates import other templates.

```yaml
$recurse_yaml
```

```bash
$ replacement -t tests/recurse.yaml
$recurse_out
```

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
