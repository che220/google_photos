#!/bin/bash

if [[ $# -lt 2 ]]; then
    echo "$0 <google acct> <client number, 1 or 2>"
    exit 1
fi

google_acct=$1
client_no=$2
token_file=token_photoslibrary_v1_${google_acct}_client_${client_no}.pickle
secret_file=client_secret_photos_${client_no}.json
list_file=photo_list_${google_acct}.csv
if [ ! -f $token_file ]; then
    echo "cannot find $token_file"
    exit 2
fi
if [ ! -f $secret_file ]; then
    echo "cannot find ${secret_file}"
    exit 3
fi
if [ ! -f $list_file ]; then
    echo "cannot find $list_file"
    exit 4
fi

ln -s -f $token_file token_photoslibrary_v1.pickle
ln -s -f $secret_file client_secret_photos.json
ln -s -f $list_file photo_list.csv
ls -l --color
