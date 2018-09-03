# Replacement

Replacement is a python utility that parses a template and outputs text.

NOTE: the examples given here are further documented in the
	[examples documentation](examples/README.md).

## Introduction

A *template* is a YAML file containing a `replacement` list
	and optionally some *variables*.

```yaml
---
# simplistic template example
# examples/hello.yaml
replacement:
  - literal: |
      hello world
...
```

```bash
$ replacement -t examples/hello.yaml
hello world
```

A *variable* is any `key: value` pair where `key` is not a Replacement keyword.
Variables encountered during parsing are assigned
	to the run-time substitutions dictionary, called the *lexicon*.
They are then available when processing text (aka: variable substitution).

```yaml
---
# variable substitution example
# examples/format.yaml
vers: 1.0
replacement:
  - literal: |
      file version {vers}
  - process: format
...
```

```bash
$ replacement -t examples/format.yaml
file version 1.0
```

Note the explicit `process` *directive* in the example above.

A *directive* is a keyword specifying an action to be executed by Replacement.
The `literal` and `process` keys above are examples of directives.

Each *block* (list item) in `replacement` must contain a directive,
	and may also contain variables and modifiers.
Blocks are executed in sequence.

```yaml
---
# show blocks being executed in sequence
# examples/sequence.yaml
vers: 1.0
replacement:
  # 'process' directive sees no lines in buffer
  - process: format
  # 'literal' then outputs to buffer
  - literal: |
      file version {vers}
  # no further directives: buffer is printed
...
```

```bash
$ replacement -t examples/sequence.yaml
file version {vers}
```

Each directive in a `replacement` list sees the *buffer* and lexicon state
	as modified by previous directives.
Directives may either `append` to or `replace` the buffer;
	each directive has an intuitive default to keep the template terse.
These may be overwritten with the `buffer` *parameter*:

```yaml
---
# show buffer mechanics
# examples/buffer.yaml
vers: 1.0
replacement:
  - literal: |
      hello
  # replaces buffer contents; the default would be to append to buffer
  - literal: |
      file version {vers}
    buffer: replace
  # appends formatted text to buffer: the default would be to replace it
  - process: format
    buffer: append
...
```

```bash
$ replacement -t examples/buffer.yaml
file version {vers}
file version 1.0
```

In the above example, `buffer` is a parameter: a keyword used to modify a directive.

The `replacement` keyword is also a directive.
This allows for recursion, which is useful in limiting how much (aka what parts)
	of the buffer and lexicon that directives can see and affect.

```yaml
---
# show recursion
# examples/recursion.yaml
vers: 1.0
name: recursion
replacement:
  - replacement:
      - literal:
          v {vers} substituted outside replacement block
      - file: |
          v{vers}.txt
        vers: 1  # clobber 'vers' in this 'replacement' block only
        substitute: format  # substitute the value of 'file' before evaluating
      - process: safe_substitute  # use string.template for '$var' constructs
  - literal: |
      file version {vers}
  - process: format
...
```

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
