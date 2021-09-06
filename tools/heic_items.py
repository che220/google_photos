"""
Convert HEIC to JPG
"""
import os
import logging
import glob
from concurrent.futures import ProcessPoolExecutor, as_completed
import traceback
import shutil

import pyheif
from PIL import Image, UnidentifiedImageError
import pandas as pd

pd.set_option('display.width', 5000)
pd.set_option('display.max_rows', 5000)
pd.set_option('display.max_colwidth', 5000)
pd.set_option('max_columns', 600)
pd.set_option('display.float_format', lambda x: '%.2f' % x)  # disable scientific notation for print

logging.basicConfig(format='%(asctime)s [%(name)s:%(lineno)d] [%(levelname)s] %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(os.path.basename(__file__))


def archive_heic(heic_file):
    file_dir = os.path.dirname(heic_file)
    file_dir = os.path.join(file_dir, 'heic')
    os.makedirs(file_dir, exist_ok=True)
    new_path = os.path.join(file_dir, os.path.basename(heic_file))
    shutil.move(heic_file, new_path)
    logger.info('moved HEIC file: %s -> %s', heic_file, new_path)


def convert_to_jpg(heic_file):
    """

    :param heic_file: input file
    :return:
    """
    outfile = heic_file.replace('.', '_') + '.jpg'
    # noinspection PyBroadException
    try:
        if not os.path.exists(outfile):
            image = Image.open(heic_file)
            image.save(outfile)
            logger.info('converted: %s -> %s %s', heic_file, outfile, image.size)
        archive_heic(heic_file)
        return outfile
    except UnidentifiedImageError:
        heif_file = pyheif.read(heic_file)
        image = Image.frombytes(heif_file.mode, heif_file.size, heif_file.data, "raw",
                                heif_file.mode, heif_file.stride, )
        image.save(outfile)
        logger.info('HEIF converted: %s -> %s %s', heic_file, outfile, image.size)
        archive_heic(heic_file)
        return outfile
    except:  # pylint: disable=bare-except
        traceback.print_exc()
        logger.info("cannot convert %s", heic_file)
        return None


def main():
    """
    entry point

    :return:
    """
    root_dir = os.path.join(os.environ['HOME'], 'TB/photos')
    heic_files = sorted(glob.glob(os.path.join(root_dir, '[0-9][0-9][0-9][0-9]-[0-9][0-9]/[0-9][0-9]/*.heic')))

    total_files = len(heic_files)
    logger.info('total %s HEIC files', total_files)

    success = 0
    failed = []
    with ProcessPoolExecutor() as executor:
        fut_to_file = {executor.submit(convert_to_jpg, file): file for file in heic_files}
        for fut in as_completed(fut_to_file):
            infile = fut_to_file[fut]
            # noinspection PyBroadException
            try:
                result = fut.result()
                if result is None:
                    failed.append(infile)
                else:
                    success += 1
            except:  # pylint: disable=bare-except
                failed.append(infile)

    logger.info('total %s heic files', total_files)
    logger.info('converted %s', success)
    logger.info('failed %s', len(failed))
    logger.info('Failed files:')
    for failure in failed:
        logger.info('\t\t%s', failure)


if __name__ == '__main__':
    main()
