import os
import cv2
from utils import get_all_files_with_extension

error_files = []
files = get_all_files_with_extension('.png')
for file in files:
    try:
        orig_size = os.path.getsize(file) / 1024 / 1024
        img = cv2.imread(file, cv2.IMREAD_UNCHANGED)

        i = file.rfind('.')
        outfile = file[0:i] + '.jpg'
        cv2.imwrite(outfile, img)
        new_size = os.path.getsize(outfile) / 1024 / 1024
        pct = 1.0 - new_size/orig_size
        
        os.remove(file)
        print(f'{file} => {outfile}, Size (MB): {orig_size:.2f} => {new_size:.2f} (saved {pct*100.0:.2f}%)')
    except:
        print("Cannot process", file)
        import traceback
        traceback.print_exc()
        
        error_files.append(file)

print("Files with errors:")
for file in error_files:
    print('\t', file)

print(f'processed {len(files)} files')
