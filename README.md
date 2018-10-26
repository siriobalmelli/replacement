# Replacement

Replacement is a python utility that parses a yaml template and outputs text.

NOTE: the examples given here are further documented in the
  [tests](tests/README.md).

## Introduction

A *template* is a YAML file containing a `replacement` object.

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

Executing a template using `replacement.py`:

```bash
$ replacement.py -t tests/hello.yaml
hello world
```

Blocks always begin with a `directive`; which specifies:
  - the data type the block will `yield`, such as `text` or a `dict`
  - the input data type, such as `file` or `yaml`

In the block above, `text: text` is the directive;
  it specifies the block takes `text` input and outputs `text`.

### 2. reading from a file

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
$ replacement.py -t tests/file.yaml
hello world
```

A few NOTES:
  - The directive in the above block is `text: file`;
    this means: "output text, input from a file".
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
    - function  # import and then call call a function
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
      message {message}
      hi {hi}
...
```

```bash
$ replacement.py -t tests/metadata.yaml
v1.1 tag "my_awesome_tag"
message hello world
hi 5
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
  # string substitution with 'proc
  - text: text
    proc: format
    input: |
      hello {hello}
      hi {hi}
      list {list}
...
```

```bash
$ replacement.py -t tests/meta_file.yaml
hello world
hi 5
list [1, 2, 3, 4]
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
  - meta: text
    input:
      version: 1.1
      tag: my_awesome_tag
  # use 'proc' to specify that 'str.format(**meta)' should be run on output
  - text: text
    proc: format
    input: |
      v{version} tag "{tag}"
  - text: text
    input:
      # metadata additions/changes seen by later blocks and any children,
      # but seen outside this list
      - meta: text
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
  - meta: text
    input: |
      ---
      filename: hello.out
      ...
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

### 6. access to python `eval` and function execution

```yaml
---
# eval and function execution
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

### 7. imports and function execution

**TODO**

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
