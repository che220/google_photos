"""
code to access google api
"""
import pickle
import os
import logging
import datetime as dt
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# silent the harmless google-auth/oauth2client error message
logger = logging.getLogger(os.path.basename(__file__))
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)


def create_service(client_secret_file, api_name, api_version, *in_scopes):
    """

    :param client_secret_file:
    :param api_name:
    :param api_version:
    :param in_scopes:
    :return:
    """
    api_service_name = api_name
    scopes = in_scopes[0]

    logger.info('CLIENT SECRET FILE: %s', client_secret_file)
    logger.info('API SERVICE NAME: %s', api_service_name)
    logger.info('API VERSION: %s', api_version)
    logger.info('SCOPES: %s', scopes)

    cred = None
    secret_dir = os.path.dirname(client_secret_file)
    pickle_file = os.path.join(secret_dir, f'token_{api_service_name}_{api_version}.pickle')

    if os.path.exists(pickle_file):
        with open(pickle_file, 'rb') as token:
            cred = pickle.load(token)

    if not cred or not cred.valid:
        if cred and cred.expired and cred.refresh_token:
            cred.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, scopes)
            cred = flow.run_local_server()

        with open(pickle_file, 'wb') as token:
            pickle.dump(cred, token)

    try:
        logger.info('CLIENT ID: %s', cred.client_id)
        service = build(api_service_name, api_version, credentials=cred)
        logger.info('%s service created successfully', api_service_name)
        return service
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception(exc)
    return None


def convert_to_rfc_datetime(year=1900, month=1, day=1, hour=0, minute=0):
    """

    :param year:
    :param month:
    :param day:
    :param hour:
    :param minute:
    :return:
    """
    converted_time = dt.datetime(year, month, day, hour, minute).isoformat() + 'Z'
    return converted_time
