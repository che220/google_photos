#!/bin/bash

if [ $# -ne 1 ]; then
    echo "$0 <year>"
    exit 1
fi

year=$1
months="Dec Nov Oct Sep Aug Jul Jun May Apr Mar Feb Jan"
for month in $months; do
    newDir="${month}-${year}"
    mkdir -p $newDir
    echo "created $newDir"
done

