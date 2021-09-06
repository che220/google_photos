#!/bin/bash

. $HOME/venvs/venv_w2/bin/activate

scriptDir=$(dirname $0)
scriptDir=$(cd $scriptDir; pwd)
echo "script dir: $scriptDir"

cmd="python $HOME/projects/google_photos/media_items.py"

function get_list()
{
    local user=$1
    echo "get list of user $user ..."
    local token_file=$scriptDir/token_photoslibrary_v1_${user}.pickle
    local list_file=$scriptDir/photo_list_${user}.csv
    if [[ -e $list_file ]]; then
	echo "$list_file exists. Skip downloading list"
	return
    fi
    ls -l token_photos* photo_list*
    echo
    run_cmd="$cmd $token_file $scriptDir $list_file"
}

users="920133 hw libin"
users="920133 hw"
for u in $users; do
    get_list $u
done
echo "All lists are downloaded"

function download_items()
{
    local user=$1
    echo "get list of user $user ..."
    local token_file=$scriptDir/token_photoslibrary_v1_${user}.pickle
    local list_file=$scriptDir/photo_list_${user}.csv
    if [[ ! -e $list_file ]]; then
	echo "$list_file does not exist. Skip downloading photos"
	return
    fi
    ls -l token_photos* photo_list*
    echo
    run_cmd="$cmd $token_file $scriptDir $list_file"
}

for u in $users; do
    download_items $u
done
echo "All photos are downloaded"

