import os
import re
import datetime as dt
import shutil

exts = set()
media_types = ['.jpg', '.tif', '.png', '.gif', '.mov', '.mp4',  '.mpg', '.heic', 'webp', '.jpeg']


def get_photos(files, in_dir):
    for file in os.listdir(in_dir):
        if file.startswith("."):
            continue

            
        file = os.path.join(in_dir, file)
        if os.path.isdir(file):
            files = get_photos(files, file)
        else:
            pos = file.rfind(".")
            if pos < 0:
                continue

            ext = file[pos:].lower()
            exts.update([ext])
            if ext not in media_types:
                continue

            created = dt.datetime.fromtimestamp(os.path.getmtime(file))
            files.append((file, created))
    return files


from_dir = os.path.join(os.environ['HOME'], 'Linux2/tmp1')
to_dir = os.path.join(os.environ['HOME'], 'TB/photos')

files = get_photos([], from_dir)
print('Number of files:', len(files))
print('All extensions:', exts)

for file, created in files:
    sub_dir = f'{created.year}-{created.month:02d}'
    filename = os.path.basename(file)
    pos = filename.rfind('.')
    if pos < 0:
        continue
    filename = filename[0:pos] + filename[pos:].lower()
    filename = re.sub(r"[()'\s-]+", '_', filename)
    to_file = os.path.join(to_dir, sub_dir, filename)
    os.makedirs(os.path.dirname(to_file), exist_ok=True)
    print(file, '->', to_file)
    shutil.move(file, to_file)
