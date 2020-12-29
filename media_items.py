"""
Download photos and videos from Google Photos
"""
from argparse import ArgumentParser
import os
import sys
import traceback
import platform
import logging
import datetime as dt
import json
import re
from signal import signal, SIGINT
from concurrent.futures import ProcessPoolExecutor
import requests

import pandas as pd

from googleapiclient.errors import HttpError

from google_api import create_service

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


def sigint_handler(recv_signal, frame):  # pylint: disable=unused-argument
    """
    handle ctrl-c

    :param recv_signal:
    :param frame:
    :return:
    """
    executor.shutdown(wait=False)
    logger.info("SIGINT or CTRL-C detected. Exiting ...")
    sys.exit(0)


def init_service(secret_dir):
    """
    start google photo service by collecting credentials etc.

    :param secret_dir:
    :return:
    """
    # look for client id JSON file and token file in work dir
    api_name = "photoslibrary"
    api_version = "v1"
    client_secret_file = os.path.join(secret_dir, 'client_secret_photos.json')
    # scopes = ['https://www.googleapis.com/auth/photoslibrary',
    #           'https://www.googleapis.com/auth/photoslibrary.sharing']
    scopes = ['https://www.googleapis.com/auth/photoslibrary']

    service = create_service(client_secret_file, api_name, api_version, scopes)
    return service


def get_batch_info(service, ids: list) -> pd.DataFrame:
    """
    batchGet requires list strictly. Other iterables cannot be used.
    """
    if len(ids) > 50:
        raise RuntimeError("max number of ids for batchGet is 50. Abort")

    resp = service.mediaItems().batchGet(mediaItemIds=ids).execute()
    results = resp['mediaItemResults']
    meta = []
    for result in results:
        meta.append(result['mediaItem'])
    batch_df = pd.DataFrame(meta)
    batch_df['created'] = batch_df.mediaMetadata.map(
        lambda x: dt.datetime.strptime(x['creationTime'], "%Y-%m-%dT%H:%M:%SZ"))
    batch_df['is_video'] = batch_df.mediaMetadata.map(lambda x: 'video' in x)
    batch_df.loc[batch_df.is_video, 'baseUrl'] += "=dv"
    batch_df.loc[~batch_df.is_video, 'baseUrl'] += "=d"
    return batch_df


def save_item(content, outfile, created, old_filename):
    """
    save content to outfile with created timestamp

    :param content:
    :param outfile:
    :param created:
    :param old_filename:
    :return:
    """
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
        raise RuntimeError('Cannot handle OS type: ' + host)
    fsize = os.path.getsize(outfile) / 1024 / 1024
    logger.info('saved into %s (was %s, created at %s, size: %.2f MB)',
                outfile, old_filename, created, fsize)


def download_photo_list(service, list_file):
    """
    download list of photos

    :param service:
    :param list_file:
    :return: pandas dataframe with photo info
    """
    logger.info('Download photo list ...')
    page_size = 100
    resp = service.mediaItems().list(pageSize=page_size).execute()
    items = resp.get('mediaItems')

    next_page_token = resp.get('nextPageToken', None)
    cnt = 0
    while next_page_token:
        resp = service.mediaItems().list(pageSize=page_size, pageToken=next_page_token).execute()
        items += resp.get('mediaItems', None)
        next_page_token = resp.get('nextPageToken', None)
        cnt += 1
        logger.info('done batch %s', cnt)

    list_df = pd.DataFrame(items)
    list_df.mediaMetadata = list_df.mediaMetadata.map(str)
    list_df.to_csv(list_file, header=True, index=False)
    logger.info('saved list file: %s (total photos: %s)', list_file, list_df.shape)


def filter_outfile(outfile):
    """
    if outfile exists, make it None so it can be filtered out

    :param outfile:
    :return:
    """
    return None if os.path.exists(outfile) else outfile


def download_items(service, item_df) -> None:
    """
    take item_df and download items one by one

    :param service:
    :param item_df:
    :return:
    """
    logger.info('working on %s to %s ...', item_df.index.min(), item_df.index.max())
    item_df.reset_index(drop=True, inplace=True)
    batch_df = get_batch_info(service, list(item_df.id))
    batch_df = batch_df.merge(item_df[['id', 'outfile']], on='id')
    assert item_df.shape[0] == batch_df.shape[0]  # make sure the rows are the same

    for _, row in batch_df.iterrows():
        item_id = row.id
        outfile = row.outfile
        url = row.baseUrl
        created = row.created
        os.makedirs(os.path.dirname(outfile), exist_ok=True)
        if os.path.exists(outfile):
            continue

        # noinspection PyBroadException
        try:
            logger.debug('get %s ...', item_id)
            sess = requests.session()
            content = sess.get(url).content
            save_item(content, outfile, created, row.filename)
        except HttpError:
            logger.error('Quota rejected downloading %s', item_id)
            traceback.print_exc()
            os.kill(os.getppid(), SIGINT)
            sys.exit(0)
        except SystemExit:
            os.kill(os.getppid(), SIGINT)
            sys.exit(0)
        except:  # pylint: disable=bare-except
            logger.error('Error downloading %s', item_id)
            traceback.print_exc()


def get_creation_time(metadata):
    """
    metadata is a JSON string. Loaded and extract "creationTime" string

    :param metadata:
    :return:
    """
    meta = metadata.replace("'", '"')  # json demands double-quote
    meta = json.loads(meta)
    return meta['creationTime']


def get_file_extension(google_filename):
    """
    the part behind the last ".", including ".". Then lower()

    :param google_filename:
    :return:
    """
    pos = google_filename.rfind('.')
    return None if pos < 0 else google_filename[pos:].lower()


def fix_filename(google_filename):
    """
    remove space, (), single-quote chars. And lower extensions

    :param google_filename:
    :return:
    """
    google_filename = re.sub(r'\s+', '_', google_filename)  # spaces to one _
    google_filename = re.sub(r'[()]+', '_', google_filename)  # () to _
    google_filename = re.sub(r'_+', '_', google_filename)  # multiple _ to one _
    google_filename = google_filename.replace("'", "_")  # ' to _
    pos = google_filename.rfind('.')  # lower extension
    return google_filename[0:pos] + google_filename[pos:].lower()  # lowercase the extension


def read_photo_list_file(service, photo_dir, download_filter_func):
    """

    :param service:
    :param photo_dir:
    :param download_filter_func: function to filter outfile
    :return:
    """
    list_file = os.path.join(photo_dir, 'photo_list.csv')
    if not os.path.exists(list_file):
        download_photo_list(service, list_file)
        sys.exit(0)

    list_file = os.path.join(photo_dir, 'photo_list.csv')
    photo_list_df = pd.read_csv(list_file)
    logger.info('loaded list from %s: %s', list_file, photo_list_df.shape)
    logger.info('dataframe structure:\n%s', photo_list_df.dtypes)

    #
    # see "photo_list_df.sample.txt" for data sample
    #
    photo_list_df['creationTime'] = photo_list_df.mediaMetadata.map(get_creation_time)
    photo_list_df['file_type'] = photo_list_df.filename.map(get_file_extension)
    photo_list_df = photo_list_df[~pd.isnull(photo_list_df.file_type)]

    def get_month_path(goole_name):
        return os.path.join(photo_dir, '-'.join(goole_name.split('-')[0:2]))
    # month: $HOME/TB/photos/2007-05
    photo_list_df['month'] = photo_list_df.creationTime.map(get_month_path)

    # filter based on original filenames
    photo_list_df['new_filename'] = photo_list_df.filename.map(fix_filename)
    # outfile: $HOME/TB/photos/2007-05/IMG_1980.jpeg
    photo_list_df['outfile'] = photo_list_df.month + '/' + photo_list_df.new_filename

    photo_list_df.outfile = photo_list_df.outfile.map(download_filter_func)
    # drop existing outfiles
    photo_list_df = photo_list_df[~pd.isnull(photo_list_df.outfile)].copy()

    photo_list_df = photo_list_df.sort_values('creationTime', ascending=False)
    photo_list_df.reset_index(drop=True, inplace=True)
    logger.debug('head:\n%s', photo_list_df.head(1))
    logger.debug('tail:\n%s', photo_list_df.tail(1))
    logger.info('%s media items to be downloaded', photo_list_df.shape[0])

    return photo_list_df


def get_output_dir():
    """

    :return: output directory
    """
    photo_dir = os.path.join(os.environ['HOME'], 'Desktop/private/photos')  # Mac
    if host.startswith('LINUX'):
        photo_dir = os.path.join(os.environ['HOME'], 'TB/photos')
    return photo_dir


def parse_args():
    """

    :return: arguments
    """
    parser = ArgumentParser()
    parser.add_argument('-s', '--sequential', action="store_true", help='sequential download')
    parser.add_argument('-t', '--token-only', action="store_true", help='get token only')
    parser.add_argument('-i', '--info-only', action="store_true", help='info only. no download')
    args = parser.parse_args()
    logger.info('options: %s', args)
    return args


def main():
    """
    app entry point

    :return:
    """
    signal(SIGINT, sigint_handler)

    args = parse_args()
    photo_dir = get_output_dir()
    service = init_service(photo_dir)
    if args.token_only:
        sys.exit(0)

    photo_list_df = read_photo_list_file(service, photo_dir, filter_outfile)
    if photo_list_df.empty:
        logger.info('All photos were downloaded. Nothing more to download.')
        sys.exit(0)

    if args.info_only:
        logger.info('File Types:\n%s',
                    photo_list_df.file_type.value_counts(dropna=False).sort_index())
        logger.info('Month Counts:\n%s',
                    photo_list_df.month.value_counts().sort_index())
        sys.exit(0)

    if args.sequential:
        logger.info("SEQUENTIAL DOWNLOAD")
    else:
        logger.info("PARALLEL DOWNLOAD")

    # baseUrl quota is 75000. But all requests quota is 10000. So we need to use batchGet
    batch_max = 50
    for st_row in range(0, photo_list_df.shape[0], batch_max):
        end_row = min(st_row + batch_max, photo_list_df.shape[0])
        item_df = photo_list_df.iloc[st_row:end_row, :].copy()

        if args.sequential:
            download_items(service, item_df)
        else:
            # noinspection PyBroadException
            try:
                executor.submit(download_items, service, item_df)
            except Exception:  # pylint: disable=broad-except
                traceback.print_exc()


if __name__ == '__main__':
    main()
