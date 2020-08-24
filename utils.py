import os, cv2, re, functools

ROOT_DIR = os.path.join(os.environ['HOME'], 'TB/photos')


@functools.lru_cache()
def get_photo_dirs():
    photo_dirs = []
    for file in os.listdir(ROOT_DIR):
        file = os.path.join(ROOT_DIR, file)
        if os.path.isdir(file):
            photo_dirs.append(file)
    return sorted(photo_dirs)


def get_all_file_extensions():
    photo_dirs = get_photo_dirs()
    extensions = []
    for in_dir in photo_dirs:
        for file in os.listdir(in_dir):
            file = os.path.join(in_dir, file)
            if os.path.isfile(file):
                i = file.rfind('.')
                if i > 0:
                    ext = file[i:]
                    if ext not in extensions:
                        extensions.append(ext)
    return sorted(extensions)


def get_all_files_with_extension(target_ext):
    """
    case insensitive
    """
    target_ext = target_ext.lower()
    photo_dirs = get_photo_dirs()
    files = []
    for in_dir in photo_dirs:
        for file in os.listdir(in_dir):
            orig_file = os.path.join(in_dir, file)
            if os.path.isfile(orig_file):
                file = file.lower()
                i = file.rfind('.')
                if i > 0:
                    ext = file[i:]
                    if ext == target_ext:
                        files.append(orig_file)
    return sorted(files)


if __name__ == "__main__":
    extensions = get_all_file_extensions()
    print(extensions)
    for ext in extensions:
        files = get_all_files_with_extension(ext)
        print(f'Extension: {ext}, \tFiles: {len(files)}')
    