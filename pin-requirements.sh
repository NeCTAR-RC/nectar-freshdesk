#!/bin/bash

# Pin a set of requirements based on OpenStack upper constraints.

if [ -z "$1" ]; then
    echo "Usage: $(basename $0) requirements.txt > requirements.lock"
    exit 1
fi

SOURCE=$1
CONSTRAINTS_BRANCH=master
CONSTRAINTS_URL="https://raw.githubusercontent.com/openstack/requirements/$CONSTRAINTS_BRANCH/upper-constraints.txt"
CONSTRAINTS_FILE=$(mktemp)

if ! $(wget -q -O"$CONSTRAINTS_FILE" "$CONSTRAINTS_URL"); then
    echo "Failed to download upstream upper-constraints.txt file."
    rm $CONSTRAINTS_FILE || true
    exit 1
fi

for line in $(cat "$1"); do
    package=$(echo $line | awk -F'=' '{print $1}')
    constraint=$(grep $package $CONSTRAINTS_FILE)
    if [ -z "$constraint" ]; then
        constraint="$line"
    fi
    echo "$constraint"
done

rm $CONSTRAINTS_FILE || true
