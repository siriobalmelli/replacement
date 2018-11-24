#!/bin/bash
pushd $(dirname $(readlink $0))
./replacement -t README.template.yaml >README.md
popd
