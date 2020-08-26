#!/bin/bash

. $HOME/venvs/venv_w2/bin/activate

cmd="python $HOME/projects/google_photos/media_items.py"

function get_list()
{
    local user=$1
    echo "get list of user $user ..."
    rm -f photo_list.csv
    ln -s -f token_photoslibrary_v1_${user}.pickle token_photoslibrary_v1.pickle
    $cmd
    mv -vf photo_list.csv photo_list_${user}.csv
}

users="920133 hw libin"
for u in $users; do
    get_list $u
done
echo "All lists are downloaded"

function download_items()
{
    local user=$1
    echo "download items of user $user ..."
    ln -s -f token_photoslibrary_v1_${user}.pickle token_photoslibrary_v1.pickle
    ln -s -f photo_list_${user}.csv photo_list.csv
    $cmd
}

for u in $users; do
    download_items $u
done
echo "All photos are downloaded"

