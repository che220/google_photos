#!/bin/bash

if [ $# -ne 1 ]; then
    echo "$0 <year>"
    exit 1
fi

year=$1
months="01 02 03 04 05 06 07 08 09 10 11 12"
for month in $months; do
    newDir="${year}-${month}"
    mkdir -p $newDir
    echo "created $newDir"
done

sudo chmod go+w ${year}-*

