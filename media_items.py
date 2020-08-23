import os
import logging
import pandas as pd
import numpy as np
import requests
import cv2
import datetime as dt
from photos import service

pd.set_option('display.width', 5000)
pd.set_option('display.max_rows', 5000)
#pd.set_option('display.max_colwidth', 5000)
pd.set_option('max_columns', 600)
pd.set_option('display.float_format', lambda x: '%.2f' % x)  # disable scientific notation for print

logger = logging.getLogger(os.path.dirname(__file__))


def show_img(img):
    logger.info("image size: %s", img.shape)
    f = img.shape[0]//1000 + 1
    w = img.shape[1]//f
    h = img.shape[0]//f
    logger.info('resize to %s x %s', w, h)
    img = cv2.resize(img, (w, h))
    cv2.imshow("Image", img)
    cv2.waitKey(0)


def get_item_info(id):
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
    img = cv2.imdecode(img, cv2.IMREAD_UNCHANGED)
    return img


def get_outfile(google_filename, created):
    pos = google_filename.rfind('.')
    outfile = google_filename + '.jpg' if pos < 0 else google_filename[0:pos] + '.jpg'
    outdir = os.path.join('photos', f'{created.year}-{created.month:02d}')
    os.makedirs(outdir, exist_ok=True)
    outfile = os.path.join(outdir, outfile)
    return outfile


def save_item(img, outfile, created):
    cv2.imwrite(outfile, img)
    created = created.strftime('%m/%d/%Y %H:%M:%S')
    os.system(f'SetFile -d "{created}" {outfile}')
    os.system(f'SetFile -m "{created}" {outfile}')
    logger.info('saved into %s', outfile)


def download_photo_list():
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


if __name__ == '__main__':
    list_file = os.path.join('photos', 'photo_list.csv')
    if not os.path.exists(list_file):
        df = download_photo_list()
        df.to_csv(list_file, header=True, index=False)
        logger.info('saved list file: %s', list_file)
    else:
        logger.info('load list from %s', list_file)
        df = pd.read_csv(list_file)

    id = df.id.iloc[0]
    url, created = get_item_info(id)
    outfile = get_outfile(df.filename.iloc[0], created)
    if os.path.exists(outfile):
        logger.info('skip %s', outfile)
    else:
        print(f'get {id} ...')
        img = download_img(url)
        save_item(img, outfile, created)
