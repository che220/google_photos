"""
Convert HEIC to JPG
"""
import os
import logging
import pandas as pd
import glob
from PIL import Image, UnidentifiedImageError
import pyheif
from concurrent.futures import ProcessPoolExecutor, as_completed
import traceback

pd.set_option('display.width', 5000)
pd.set_option('display.max_rows', 5000)
pd.set_option('display.max_colwidth', 5000)
pd.set_option('max_columns', 600)
pd.set_option('display.float_format', lambda x: '%.2f' % x)  # disable scientific notation for print

logging.basicConfig(format='%(asctime)s [%(name)s:%(lineno)d] [%(levelname)s] %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(os.path.basename(__file__))


def convert_to_jpg(heic_file):
    outfile = heic_file.replace('.', '_') + '.jpg'
    try:
        if not os.path.exists(outfile):
            im = Image.open(heic_file)
            im.save(outfile)
            logger.info('converted: %s -> %s %s', heic_file, outfile, im.size)
        return outfile
    except UnidentifiedImageError:
        heif_file = pyheif.read(heic_file)
        im = Image.frombytes(heif_file.mode, heif_file.size, heif_file.data, "raw",
                             heif_file.mode, heif_file.stride,)
        im.save(outfile)
        logger.info('HEIF converted: %s -> %s %s', heic_file, outfile, im.size)
        return outfile
    except:
        traceback.print_exc()
        logger.info("cannot convert %s", heic_file)
        return None


def main():
    root_dir = os.path.join(os.environ['HOME'], 'TB/photos')
    heic_files = sorted(glob.glob(os.path.join(root_dir, '[0-9][0-9][0-9][0-9]-[0-9][0-9]/*.heic')))

    total_files = len(heic_files)
    logger.info('total %s HEIC files', total_files)

    success = 0
    failed = []
    cnt = 0
    with ProcessPoolExecutor() as executor:
        fut_to_file = {executor.submit(convert_to_jpg, file): file for file in heic_files}
        for fut in as_completed(fut_to_file):
            infile = fut_to_file[fut]
            try:
                result = fut.result()
                if result is None:
                    failed.append(infile)
                else:
                    success += 1
            except:
                failed.append(infile)

    logger.info('total %s heic files', total_files)
    logger.info('converted %s', success)
    logger.info('failed %s', len(failed))
    logger.info('Failed files:')
    [logger.info('\t\t%s', f) for f in failed]


if __name__ == '__main__':
    main()
