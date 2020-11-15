import os
import logging
from google_api import create_service

logging.basicConfig(format='%(asctime)s [%(name)s:%(lineno)d] [%(levelname)s] %(message)s',
                    level=logging.INFO)


def init_service(secret_dir):
    # look for client id JSON file and token file in work dir
    api_name = "photoslibrary"
    api_version = "v1"
    client_secret_file = os.path.join(secret_dir, 'client_secret_photos.json')
    scopes = ['https://www.googleapis.com/auth/photoslibrary', 'https://www.googleapis.com/auth/photoslibrary.sharing']

    service = create_service(client_secret_file, api_name, api_version, scopes)
    # print(dir(service))
    return service
