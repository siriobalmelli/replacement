#!/bin/bash

pushd $(dirname $(readlink $0))

FAIL=""
PASS=""

for a in *.yaml; do
	yamllint "$a"
	if ../replacement.py -t "$a" >"${a%.yaml}.temp" \
		&& diff "${a%.yaml}.temp" "${a%.yaml}.out"
	then
		PASS="${PASS}$a\n"
	else
		FAIL="${FAIL}$a\n"
	fi
	rm -f "${a%.yaml}.temp"
done

# flush current stdout (if user is watching all logs)
echo -e "\nPASS:\n$PASS" >&2

if [[ $FAIL ]]; then
	echo -e "FAIL:\n$FAIL" >&2
	exit 1
fi
exit 0

popd
