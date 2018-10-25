# Replacement

Replacement is a python utility that parses a yaml template and outputs text.

NOTE: the examples given here are further documented in the
  [tests](tests/README.md).

## Introduction

A *template* is a YAML file containing a `replacement` object.

A replacement object contains a list of `blocks`.

```yaml
---
# simplistic template example
# examples/hello.yaml
replacement:
  - text: text
    input:
      hello world
...
```

```bash
$ replacement -t examples/hello.yaml
hello world
```

Blocks always begin with a `directive`; which specifies:
  - the data type the block will `yield`, such as `text` or a `dict`
  - the input data type, such as `file` or `yaml`

In the block above, `text: text` is the directive;
  it specifies the block takes `text` input and outputs `text`.

Here is an example that reads from a file:

```yaml
---
# read from file
# examples/file.yaml
replacement:
  - text: file
    input:
      hello.out
...
```

```bash
$ replacement -t examples/file.yaml
hello world
```

A few NOTES:
  - The directive is now `text: file`.
    This means: "output text, input from a file"
  - The `input` key is now used for the filename to be read;
    in the first example `input` was used to store the literal text input.
  - File paths are relative to the path of the template.

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
    - function  # import and then call call a function
    - exec  # subprocess execution (usually bash)

  inputVal: input_specific
...
```

Blocks are executed in sequence, and may nest:

```yaml
---
# nesting blocks
# examples/nesting.yaml
replacement:
  # insert '1.1' into metadata (substitutions dict) under the key 'version'
  - meta: text
    spec: version
    input: 1.1
  - text: text
    proc: format
    input: |
      version {version}
  - text: text
    input:
      # metadata additions/changes seen by later blocks and any children,
      # but seen outside this list
      - meta: text
        spec: version
        input: 1.0
      - text: text
        proc: format
        input: |
          version {version} is clobbered in inner scope
      - text: file
        input:
          hello.out
  - text: text
    proc: format
    input: |
      outer version is still {version}
...
```

```bash
$ replacement -t examples/nesting.yaml
hello world
```

Blocks may contain objects (dictionaries) which may be:
    - valid YAML/JSON objects under 'input'
    -



```bash
$ cat examples/v1.txt
$name v$vers
$ replacement -t example.yaml
v 1.0 substituted outside replacement block
recursion v1
file version 1.0
```

The above example has a few details to unpack:

1. The modifier `substitute` was used to tell Replacement
  that all values in the current `file` block (e.g. `1` and `v{vers}.txt`)
  should be subtituted using Python `str.format()` before being parsed.

1. The variable `vers` is clobbered (set to `1` instead of `1.0`).
This clobbered value of `vers` not seen outside the inner (recursive)
  `replacement` list.

1. We used a different `process` method: `safe_substitute` from Python's
  `string.template`.
The `{vers}` token in `v {vers} substituted outside replacement block`
  will be output as-is by the `replacement` block and will then
  be substituted by the later `process` directive, which uses `str.format()`.

## Nomenclature

To avoid ambiguities, certain words are given specific meanings in
  the documentation and source code comments of this project.

Detailed definitions are introduced in the preceding section, with the word
  in question *italicized* where first encountered and then where defined.
A summary table is given below for reference:

| term        | definition                      | usage/example                |
| ----------- | ------------------------------- | ---------------------------- |
| Replacement | this python utility             | `$ replacement -t a.yaml`    |
| template    | YAML processed by Replacement   | [a template](template.yaml)  |
| lexicon     | runtime dict of key:value pairs | `{ "v": 1.0, "hi": "five" }` |
| variable    | one key:value pair in template  | `v: 1.0`                     |
| block       | item in a `replacement` list    | `- literal: "hello"`         |
| directive   | an action to be taken           | `file: a_file.txt`           |
| parameter   | modifier to a directive         | `substitute: format`         |

## Architecture

Blocks are processed one at a time, in this order:

1. Variables are first evluated and added to the runtime lexicon
  - variables may themselves be process
  - setting a variable again clobbers (replaces) the original value

1. Directives are then processed sequentially.
  Directives may:
- add/set variables in the lexicon:

  ```yaml
  - literal: |
      This text will be output literally.
  ```

- output text
- process previously output text
- provide a recursive block

Some differences between Replacement and other templating systems:

1. Processed sequentially (imperative, not declarative):
  - terse and intuitive grammar
  - fast (single-pass) processing
  - inconsistencies permitted (e.g. clobbering/changing variables mid-flight)
  - self-substitution (values in the template itself can be Replaced at runtime)

1. Powerful text transformation/replacement facilities

1. Template is "outermost":
- a template *may* contain some or all of the output (or may generate/source

## TODO

Project TODO list

1. Packaging:
	- Nix (including test runner)
	- Travis
	- PyPy

1. Dependency output command: runs all preprocessing and outputs a list of
  file dependencies.
For use e.g. in Makefiles.

1. Express [the schema](./schema.yaml) formally and write validation code for it.
