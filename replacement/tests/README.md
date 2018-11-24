# Template Tests Directory

Each `.yaml` template file in [this tests directory](./)
	has a corresponding `.out` file giving the expected output.

Any other files are static input for one or more templates.

All examples from the [project documentation](../README.md) should show
	the file path in this directory as a comment and be kept synchronized.

- These test cases double as examples.
- Examples which are not referenced and explained elsewhere in the
	documentation should have a section in this README.

1. Base case: no output directives results in no output
    - see [nothing.yaml](./nothing.yaml)

1. Working with dictionaries
    - see [dict.yaml](./dict.yaml)
    - see [dict_file.yaml](./dict_file.yaml)

1. Substituting function arguments when 'prep' directive is given
    - see [func_prep.yaml](./func_prep.yaml)

1. Populating 'meta' from file contents
    - see [file_as_meta.yaml](./file_as_meta.yaml)
    - see [yaml_as_meta.yaml](./yaml_as_meta.yaml)
