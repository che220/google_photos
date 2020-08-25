import os
import traceback
import platform
import logging
import pandas as pd
import numpy as np
import requests
import cv2
import datetime as dt
import json
import re
import threading
from signal import signal, SIGINT
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import multiprocessing

from Google import Create_Service
from googleapiclient.errors import HttpError

pd.set_option('display.width', 5000)
pd.set_option('display.max_rows', 5000)
#pd.set_option('display.max_colwidth', 5000)
pd.set_option('max_columns', 600)
pd.set_option('display.float_format', lambda x: '%.2f' % x)  # disable scientific notation for print

logging.basicConfig(format='%(asctime)s [%(name)s:%(lineno)d] [%(levelname)s] %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(os.path.dirname(__file__))
host = platform.platform().upper()
#lock = threading.Lock()
executor = ProcessPoolExecutor(max_workers=4)

# TODO: remove files without extension in the YYYY-MM directories

def sigint_handler(recv_signal, frame):
    executor.shutdown(wait=False)
    logger.info("SIGINT or CTRL-C detected. Exiting ...")
    exit(0)


def init_service(secret_dir):
    # look for client id JSON file and token file in work dir
    API_NAME = "photoslibrary"
    API_VERSION = "v1"
    CLIENT_SECRET_FILE = os.path.join(secret_dir, 'client_secret_photos.json')
    # SCOPES = ['https://www.googleapis.com/auth/photoslibrary', 'https://www.googleapis.com/auth/photoslibrary.sharing']
    SCOPES = ['https://www.googleapis.com/auth/photoslibrary']

    service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)
    # print(dir(service))
    return service


def show_img(img):
    logger.info("image size: %s", img.shape)
    f = img.shape[0]//1000 + 1
    w = img.shape[1]//f
    h = img.shape[0]//f
    logger.info('resize to %s x %s', w, h)
    img = cv2.resize(img, (w, h))  # pylint: disable=no-member
    cv2.imshow("Image", img)  # pylint: disable=no-member
    cv2.waitKey(0)  # pylint: disable=no-member


def get_item_info(service, id):
    # with lock:
    # google photos API is not thread-safe
    resp = service.mediaItems().get(mediaItemId=id).execute()
    meta = resp['mediaMetadata']
    logger.debug('%s', meta)
    created = dt.datetime.strptime(meta['creationTime'], "%Y-%m-%dT%H:%M:%SZ")

    url = resp['baseUrl']
    if 'video' in meta:
        url += "=dv"
    else:
        url += "=d"
    return url, created


def save_item(content, outfile, created, old_filename):
    with open(outfile, 'wb') as fout:
        fout.write(content)

    if host.startswith('DARWIN'):
        logger.debug('It is Mac')
        created = created.strftime('%m/%d/%Y %H:%M:%S')
        os.system(f'SetFile -d "{created}" {outfile}')
        os.system(f'SetFile -m "{created}" {outfile}')
    elif host.startswith('LINUX'):
        logger.debug('It is Linux')
        created = created.strftime('%Y%m%d%H%M')
        os.system(f'touch -a -m -t {created} {outfile}')
    else:
        raise RuntimeError('Cannot handle OS type: '+host)
    logger.info('saved into %s (was %s, created at %s)', outfile, old_filename, created)


def download_photo_list(service):
    page_size = 100
    resp = service.mediaItems().list(pageSize=page_size).execute()
    items = resp.get('mediaItems')

    next_page_token = resp.get('nextPageToken', None)
    cnt=0
    while next_page_token:
        resp = service.mediaItems().list(pageSize=page_size, pageToken=next_page_token).execute()
        items += resp.get('mediaItems', None)
        next_page_token = resp.get('nextPageToken', None)
        cnt += 1
        logger.info('done batch %s', cnt)

    df = pd.DataFrame(items)
    return df


def filter_outfiles(outfiles, creation_times):
    """
    if outfile exists and timestamp diff more than one day, get a new name
    """
    new_outfiles = []
    for i in range(outfiles.shape[0]):
        outfile = outfiles[i]
        if os.path.exists(outfile):
            outfile = None
        new_outfiles.append(outfile)

    return new_outfiles


def download_item(service, row):
    id = row.id
    outfile = row.outfile
    os.makedirs(os.path.dirname(outfile), exist_ok=True)
    if os.path.exists(outfile):
        return None

    try:
        logger.debug(f'get {id} ...')
        sess = requests.session()
        url, created = get_item_info(service, id)  # somehow info has to be downloaded before image can be downloaded
        content = sess.get(url).content
        save_item(content, outfile, created, row.filename)
        return None
    except HttpError:
        logger.error('Quota rejected downloading %s', id)
        traceback.print_exc()
        os.kill(os.getppid(), SIGINT)
        exit(0)
    except SystemExit:
        os.kill(os.getppid(), SIGINT)
        exit(0)
    except:
        logger.error('Error downloading %s', id)
        traceback.print_exc()
        return id


def get_creation_time(metadata):
    meta = metadata.replace("'", '"')  # json demands double-quote
    meta = json.loads(meta)
    return meta['creationTime']


def get_file_extension(google_filename):
    pos = google_filename.rfind('.')
    return None if pos < 0 else google_filename[pos:].lower()


def fix_filename(google_filename):
    google_filename = re.sub(r'\s+', '_', google_filename)
    google_filename = re.sub(r'[()]+', '_', google_filename)
    google_filename = re.sub(r'_+', '_', google_filename)
    google_filename = google_filename.replace("'", "_")
    pos = google_filename.rfind('.')
    return google_filename[0:pos] + google_filename[pos:].lower()  # lowercase the extension

    
if __name__ == '__main__':
    import sys
    signal(SIGINT, sigint_handler)
    sequential = False
    token_only = False
    if len(sys.argv) > 1:
        if '-h' in sys.argv:
            logger.info("Usage: python %s [-h] [-t] [-s]", sys.argv[0])
            logger.info("    -h: help")
            logger.info("    -s: sequential")
            logger.info("    -t: get token only")
            exit(0)

        sequential = ('-s' in sys.argv)
        token_only = ('-t' in sys.argv)
    logger.info('TOKEN ONLY: %s', token_only)

    photo_dir = os.path.join(os.environ['HOME'], 'Desktop/private/photos')  # Mac
    if host.startswith('LINUX'):
        photo_dir = os.path.join(os.environ['HOME'], 'TB/photos')
    service = init_service(photo_dir)
    if token_only:
        exit(0)

    list_file = os.path.join(photo_dir, 'photo_list.csv')
    if not os.path.exists(list_file):
        df = download_photo_list(service)
        df.mediaMetadata = df.mediaMetadata.map(str)
        df.to_csv(list_file, header=True, index=False)
        logger.info('saved list file: %s', list_file)
    else:
        logger.info('load list from %s', list_file)
        df = pd.read_csv(list_file)
    
    df['creationTime'] = df.mediaMetadata.map(get_creation_time)
    df['file_type'] = df.filename.map(get_file_extension)
    logger.info('File Types:\n%s', df.file_type.value_counts(dropna=False))

    # do not download video files yet!
    df = df[~pd.isnull(df.file_type)]
    logger.info('Remaining File Types:\n%s', df.file_type.value_counts(dropna=False))

    df['month'] = df.creationTime.map(lambda x: os.path.join(photo_dir, '-'.join(x.split('-')[0:2])))

    # filter based on original filenames
    df['new_filename'] = df.filename.map(fix_filename)
    df['outfile'] = df.month + '/' + df.new_filename
    df['orig_outfile_new'] = filter_outfiles(df.outfile.values, df.creationTime.values)
    df = df[~pd.isnull(df.orig_outfile_new)].copy()

    bad_id_file = os.path.join(photo_dir, 'bad_ids.json')
    if os.path.exists(bad_id_file):
        with open(bad_id_file, 'r') as fin:
            bad_ids = json.load(fin)
    else:
        bad_ids = []
    df = df[~df.id.isin(bad_ids)].reset_index(drop=True)
    logger.info('%s photos to be downloaded after removing bad ids', df.shape[0])

    df = df.sort_values('creationTime', ascending=False).reset_index(drop=True)
    logger.debug('head:\n%s', df.head(1))
    logger.debug('tail:\n%s', df.tail(1))
    # exit(0)

    if sequential:
        logger.info("SEQUENTIAL DOWNLOAD")
        for i, row in df.iterrows():
            id = download_item(service, row)
            if id is None:
                continue
            if id == 'exit':
                break

            bad_ids.append(id)
            with open(bad_id_file, 'w') as fout:
                fout.write(json.dumps(bad_ids, indent=4))
                logger.info('Bad ids are stored in %s', bad_id_file)
    else:
        logger.info("PARALLEL DOWNLOAD")
        for i, row in df.iterrows():
            try:
                executor.submit(download_item, service, row)
            except:
                traceback.print_exc()
                continue
