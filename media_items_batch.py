import os
import pandas as pd
import json

from google_api import create_service

pd.set_option('display.width', 5000)
pd.set_option('display.max_rows', 5000)
# pd.set_option('display.max_colwidth', 5000)
pd.set_option('max_columns', 600)
pd.set_option('display.float_format', lambda x: '%.2f' % x)  # disable scientific notation for print


def init_service(secret_dir):
    # look for client id JSON file and token file in work dir
    api_name = "photoslibrary"
    api_version = "v1"
    client_secret_file = os.path.join(secret_dir, 'client_secret_photos.json')
    # scopes = ['https://www.googleapis.com/auth/photoslibrary',
    #           'https://www.googleapis.com/auth/photoslibrary.sharing']
    scopes = ['https://www.googleapis.com/auth/photoslibrary']

    service = create_service(client_secret_file, api_name, api_version, scopes)
    # print(dir(service))
    return service


def get_creation_time(metadata):
    meta = metadata.replace("'", '"')  # json demands double-quote
    meta = json.loads(meta)
    return meta['creationTime']


def get_file_extension(google_filename):
    pos = google_filename.rfind('.')
    return None if pos < 0 else google_filename[pos:].lower()


def main():
    photo_dir = os.path.join(os.environ['HOME'], 'TB/photos')
    service = init_service(photo_dir)

    list_file = os.path.join(photo_dir, 'photo_list.csv')
    df = pd.read_csv(list_file)

    ids = list(df.id)[0:50]
    resp = service.mediaItems().batchGet(mediaItemIds=ids).execute()
    meta = resp['mediaItemResults']
    print(len(meta))
    a = meta[0]['mediaItem']


if __name__ == '__main__':
    main()
