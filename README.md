# Replacement

Replacement is a python utility that parses a template and outputs text.

A template is a YAML file containing nested blocks.

Each block may contain:
- variables
- directives

## Nomenclature

To avoid ambiguities, certain words are given specific meanings in
	the documentation and source code comments of this project.

They are defined here:

| term        | definition                      | usage/example                |
| Replacement | this python utility             | `$ replacement -t a.yaml`    |
| template    | YAML processed by Replacement   | [a template](template.yaml)  |
| lexicon     | runtime dict of key:value pairs | `{ "v": 1.0, "hi": "five" }` |
| variable    | one key:value pair in template  | `v: 1.0`                     |
| directive   | an action to be taken           | `file: a_file.txt`           |
| block       |                                 |                              |
| process     |                                 |                              |

## Architecture

Blocks are processed one at a time, in this order:

1. Variables are first evluated and added to the runtime lexicon:
	- variables may themselves be process
	- setting a variable again clobbers (replaces) the original value

1. Directives are then processed sequentially. A directive may:
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

## Keywords

All keywords used by Replacement are listed in the table below.

| directive | definition                | notes |
| output    | iterate through all child |       |
