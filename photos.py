import os
from Google import Create_Service
import pandas as pd

# look for client id JSON file and token file in work dir
work_dir = os.path.join(os.environ['HOME'], 'Desktop/private')
os.chdir(work_dir)

API_NAME = "photoslibrary"
API_VERSION = "v1"
CLIENT_SECRET_FILE = 'client_secret_photos.json'
SCOPES = ['https://www.googleapis.com/auth/photoslibrary', 'https://www.googleapis.com/auth/photoslibrary.sharing']

service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)
print(dir(service))
