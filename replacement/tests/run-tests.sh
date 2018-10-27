#!/bin/bash

set -e

pushd $(dirname $(readlink $0))

for a in *.yaml; do
	yamllint "$a"
	diff <(../replacement.py -t "$a") "${a%.yaml}.out"
	echo "$a"
done

popd
