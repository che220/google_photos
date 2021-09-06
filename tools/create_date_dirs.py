import os
import sys
from pathlib import Path
import shutil
import re
import json
import pandas as pd
import numpy as np

pd.set_option('display.width', 5000)
pd.set_option('display.max_rows', 5000)
pd.set_option('display.max_colwidth', 5000)
pd.set_option('max_columns', 600)
pd.set_option('display.float_format', lambda x: '%.2f' % x)  # disable scientific notation for print

photo_dir = sys.argv[1]
list_filename = sys.argv[2]
list_file = Path(photo_dir, list_filename)
if not list_file.exists():
    print('cannot find', list_file)
    exit(1)


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


def get_creation_date(x):
    x = x.replace("'", '"')
    t = json.loads(x)['creationTime']
    return t[8:10]


def get_creation_month(x):
    x = x.replace("'", '"')
    t = json.loads(x)['creationTime']
    return t[:7]


def curr_file_path(filename, month):
    filename = fix_filename(filename)
    file_path = Path(photo_dir, month, filename)
    if not os.path.exists(file_path):
        return ''
    return str(file_path)


def new_file_path(filename, month, date):
    filename = fix_filename(filename)
    file_path = Path(photo_dir, month, date, filename)
    return str(file_path)


list_df = pd.read_csv(list_file)
list_df['create_date'] = list_df.mediaMetadata.map(lambda x: get_creation_date(x))
list_df['create_month'] = list_df.mediaMetadata.map(lambda x: get_creation_month(x))
print(list_df.tail(10))

mat = list_df[['filename', 'create_month']].values
vfunc = np.vectorize(curr_file_path)
curr_file_paths = vfunc(mat[:, 0], mat[:, 1])
print(curr_file_paths[:10])

mat = list_df[['filename', 'create_month', 'create_date']].values
vfunc = np.vectorize(new_file_path)
new_file_paths = vfunc(mat[:, 0], mat[:, 1], mat[:, 2])
print(new_file_paths[:10])

for i in range(len(curr_file_paths)):
    curr_path = curr_file_paths[i]
    if curr_path == '':
        continue

    if not os.path.exists(curr_path):
        print('missing', curr_path)
        continue

    new_path = new_file_paths[i]
    new_dir = os.path.dirname(new_path)
    os.makedirs(new_dir, exist_ok=True)
    shutil.move(curr_path, new_path)
    print('Moved:', curr_path, '->', new_path)

