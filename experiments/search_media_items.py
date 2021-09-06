import os
import sys
import platform
import logging
from concurrent.futures import ProcessPoolExecutor

import pandas as pd
import requests

from experiments.google_api_exp import create_service

pd.set_option('display.width', 5000)
pd.set_option('display.max_rows', 5000)
pd.set_option('display.max_colwidth', 5000)
pd.set_option('max_columns', 600)
pd.set_option('display.float_format', lambda x: '%.2f' % x)  # disable scientific notation for print

logging.basicConfig(format='%(asctime)s [%(name)s:%(lineno)d] [%(levelname)s] %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(os.path.basename(__file__))
host = platform.platform().upper()
# lock = threading.Lock()
executor = ProcessPoolExecutor(max_workers=4)


def init_service(client_secret_file):
    """
    start google photo service by collecting credentials etc.

    :param client_secret_file:
    :return:
    """
    # look for client id JSON file and token file in work dir
    api_name = "photoslibrary"
    api_version = "v1"
    # scopes = ['https://www.googleapis.com/auth/photoslibrary',
    #           'https://www.googleapis.com/auth/photoslibrary.sharing']
    scopes = ['https://www.googleapis.com/auth/photoslibrary']

    service = create_service(client_secret_file, api_name, api_version, scopes)
    return service


def download_photo_list(service, list_file):
    """
    download list of photos

    :param service:
    :param list_file:
    :return: pandas dataframe with photo info
    """
    logger.info('Download photo list ...')
    page_size = 100
    filters = {
        "dateFilter": {
            "ranges": {
                "startDate": {"year": 2021, "month": 9, "day": 1},
                "endDate": {"year": 2021, "month": 9, "day": 5},
            }
        }
    }
    resp = service.mediaItems().search().execute()
    items = resp.get('mediaItems')

    next_page_token = resp.get('nextPageToken', None)
    cnt = 0
    while next_page_token:
        resp = service.mediaItems().search().execute()
        items += resp.get('mediaItems', None)
        next_page_token = resp.get('nextPageToken', None)
        cnt += 1
        logger.info('done batch %s', cnt)

    list_df = pd.DataFrame(items)
    list_df.mediaMetadata = list_df.mediaMetadata.map(str)
    list_df.to_csv(list_file, header=True, index=False)
    logger.info('saved list file: %s (total photos: %s)', list_file, list_df.shape)


def raw_login():
    from apiclient import discovery
    import httplib2
    from oauth2client import client
    import pickle
    import requests_oauthlib
    import json

    client_secret_file = '/home/hui/TB/photos/client_secret_92.json'
    with open(client_secret_file, 'r') as fin:
        client_config = json.load(fin)
    client_type = 'installed'
    client_id = client_config["installed"]["client_id"]
    scopes = ['https://www.googleapis.com/auth/photoslibrary']
    session = requests_oauthlib.OAuth2Session(client_id=client_id, scope=scopes)


def handle_raw_credential(token_file):
    import pickle
    import json
    import urllib
    import datetime as dt

    with open(token_file, 'rb') as token:
        cred = pickle.load(token)

    scopes = ['https://www.googleapis.com/auth/photoslibrary']
    body = {
        "grant_type": 'refresh_token',
        "client_id": cred.client_id,
        "client_secret": cred.client_secret,
        "refresh_token": cred.refresh_token,
        "scope" : " ".join(scopes),
    }

    headers = {"Content-Type": 'application/json'}
    resp = requests.post(url=cred.token_uri, headers=headers, json=body)
    response_data = resp.json()
    """
    look like this:
    {
        "access_token": "ya29.a0ARrdaM_J7RnIyOSYluGbpAsSOJHsVERC7wpWVG823Bg16PbFGH6txdWCLfX7x5bAUydY7MEMhHRF9e8dZceFnBq7egY8dRTKxO2DY8zByXzdJVV7hK_ioUXLytf8q4TAmIbG_0lOgou8Yh-lx6-97Az1tr9LZ4I",
        "expires_in": 3599,
        "scope": "https://www.googleapis.com/auth/photoslibrary",
        "token_type": "Bearer"
    }
    """
    print(json.dumps(response_data, indent=4))

    access_token = response_data["access_token"]
    refresh_token = response_data.get("refresh_token", cred.refresh_token)

    expires_in = response_data.get("expires_in", None)
    expiry = dt.datetime.utcnow() + dt.timedelta(seconds=expires_in)

    headers = {'Content-type': 'application/json', 'Authorization': f'Bearer {access_token}', "scope": "https://www.googleapis.com/auth/photoslibrary"}
    resp = requests.get('https://photoslibrary.googleapis.com/v1/mediaItems')

    return cred, access_token


def main():
    logger.info('%s', sys.argv)
    token_file = sys.argv[1]
    photo_list_file = os.path.join(os.environ['HOME'], 'tmp', 'list.csv')
    logger.info('Token file: %s', token_file)

    handle_raw_credential(token_file)

    # credentials = client.credentials_from_clientsecrets_and_code(
    #     client_secret_file,
    #     ['https://www.googleapis.com/auth/drive.appdata', 'profile', 'email'],
    #     auth_code)

    service, credentials = init_service(token_file)
    import requests
    headers = {'Content-type': 'application/json', 'Authorization': f'Bearer {credentials.refresh_token}'}
    resp = requests.get('https://photoslibrary.googleapis.com/v1/mediaItems')
    content = resp.content
    download_photo_list(service, photo_list_file)


if __name__ == '__main__':
    main()
