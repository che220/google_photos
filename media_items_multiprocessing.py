import os
import platform
import logging
import pandas as pd
import numpy as np
import requests
import cv2
import datetime as dt
import json
from concurrent.futures import ProcessPoolExecutor

from Google import Create_Service

pd.set_option('display.width', 5000)
pd.set_option('display.max_rows', 5000)
#pd.set_option('display.max_colwidth', 5000)
pd.set_option('max_columns', 600)
pd.set_option('display.float_format', lambda x: '%.2f' % x)  # disable scientific notation for print

logging.basicConfig(format='%(asctime)s [%(name)s:%(lineno)d] [%(levelname)s] %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(os.path.dirname(__file__))
host = platform.platform().upper()


def init_service(secret_dir):
    # look for client id JSON file and token file in work dir
    API_NAME = "photoslibrary"
    API_VERSION = "v1"
    CLIENT_SECRET_FILE = os.path.join(secret_dir, 'client_secret_photos.json')
    SCOPES = ['https://www.googleapis.com/auth/photoslibrary', 'https://www.googleapis.com/auth/photoslibrary.sharing']

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
    resp = service.mediaItems().get(mediaItemId=id).execute()
    meta = resp['mediaMetadata']
    created = dt.datetime.strptime(meta['creationTime'], "%Y-%m-%dT%H:%M:%SZ")

    w = meta['width']
    h = meta['height']

    url = resp['baseUrl']
    url = f'{url}=w{w}-h{h}'
    return url, created


def download_img(url):
    resp = requests.get(url)
    img = np.asarray(bytearray(resp.content), dtype="uint8")
    img = cv2.imdecode(img, cv2.IMREAD_UNCHANGED)  # pylint: disable=no-member
    return img


def get_outfile(google_filename, created):
    pos = google_filename.rfind('.')
    outfile = google_filename + '.jpg' if pos < 0 else google_filename[0:pos] + '.jpg'
    outfile = os.path.join(f'{created.year}-{created.month:02d}', outfile)
    return outfile


def save_item(img, outfile, created):
    cv2.imwrite(outfile, img)  # pylint: disable=no-member
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
    logger.info('saved into %s', outfile)


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


def get_unique_filename(outfile, created):
    """
    if outfile exists and timestamp diff more than one day, get a new name
    """
    idx = 0
    while 1:
        if not os.path.exists(outfile):
            return outfile
        
        mtime = os.path.getmtime(outfile)
        mtime = dt.datetime.fromtimestamp(mtime)
        gap = (created - mtime).total_seconds()
        if gap < 86400:
            logger.info('skip %s', outfile)
            return None

        pos = outfile.rfind('.')
        outfile = outfile[0:pos] + f"_{idx}" + ".jpg"
        idx += 1


def download_item(service, row):
    id = row.id
    meta = row.mediaMetadata.replace("'", '"')  # json demands double-quote
    meta = json.loads(meta)
    created = dt.datetime.strptime(meta['creationTime'], "%Y-%m-%dT%H:%M:%SZ")

    outfile = get_outfile(row.filename, created)
    outfile = os.path.join(photo_dir, outfile)
    orig_outfile = outfile
    outfile = get_unique_filename(outfile, created)
    if outfile is None:
        return

    if outfile != orig_outfile:
        logger.info('filename changed: %s', outfile)
        
    os.makedirs(os.path.dirname(outfile), exist_ok=True)

    logger.debug(f'get {id} ...')
    url, created = get_item_info(service, id)  # somehow info has to be downloaded before image can be downloaded
    img = download_img(url)
    try:
        save_item(img, outfile, created)
    except:
        import traceback
        traceback.print_exc()

    
if __name__ == '__main__':
    photo_dir = os.path.join(os.environ['HOME'], 'Desktop/private/photos')  # Mac
    if host.startswith('LINUX'):
        photo_dir = os.path.join(os.environ['HOME'], 'TB/tmp/hw_photos')
    service = init_service(photo_dir)

    list_file = os.path.join(photo_dir, 'photo_list.csv')
    if not os.path.exists(list_file):
        df = download_photo_list(service)
        df.to_csv(list_file, header=True, index=False)
        logger.info('saved list file: %s', list_file)
    else:
        logger.info('load list from %s', list_file)
        df = pd.read_csv(list_file)

    for i, row in df.iterrows():
        download_item(service, row)
