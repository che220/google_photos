#!/bin/bash

if [ $# -lt 1 ]; then
    echo "$0 <dir>"
    exit 1
fi

inDir=$1
cd $inDir
find -name "*.zip" -exec unzip -o {} \;

