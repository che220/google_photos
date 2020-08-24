#!/bin/bash

if [[ $# -lt 2 ]]; then
    echo "$0 <google acct> <client number, 1 or 2>"
    exit 1
fi

google_acct=$1
client_no=$2
ln -s -f token_photoslibrary_v1_${google_acct}_client_${client_no}.pickle token_photoslibrary_v1.pickle
ln -s -f client_secret_photos_${client_no}.json client_secret_photos.json
ln -s -f photo_list_${google_acct}.csv photo_list.csv
ls -l
