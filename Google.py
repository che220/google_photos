import pickle
import os
import logging
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

logger = logging.getLogger(os.path.dirname(__file__))
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)


def Create_Service(client_secret_file, api_name, api_version, *scopes):
    CLIENT_SECRET_FILE = client_secret_file
    API_SERVICE_NAME = api_name
    API_VERSION = api_version
    SCOPES = [scope for scope in scopes[0]]

    logger.info('CLIENT SECRET FILE: %s', CLIENT_SECRET_FILE)
    logger.info('API SERVICE NAME: %s', API_SERVICE_NAME)
    logger.info('API VERSION: %s', API_VERSION)
    logger.info('SCOPES: %s', SCOPES)    
 
    cred = None
    secret_dir = os.path.dirname(client_secret_file)
    pickle_file = os.path.join(secret_dir, f'token_{API_SERVICE_NAME}_{API_VERSION}.pickle')
 
    if os.path.exists(pickle_file):
        with open(pickle_file, 'rb') as token:
            cred = pickle.load(token)
 
    if not cred or not cred.valid:
        if cred and cred.expired and cred.refresh_token:
            cred.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            cred = flow.run_local_server()
 
        with open(pickle_file, 'wb') as token:
            pickle.dump(cred, token)
 
    try:
        logger.info('CLIENT ID: %s', cred.client_id)
        service = build(API_SERVICE_NAME, API_VERSION, credentials=cred)
        logger.info('%s service created successfully', API_SERVICE_NAME)
        return service
    except Exception as e:
        logger.exception(e)
    return None
 
 
def convert_to_RFC_datetime(year=1900, month=1, day=1, hour=0, minute=0):
    dt = datetime.datetime(year, month, day, hour, minute, 0).isoformat() + 'Z'
    return dt
