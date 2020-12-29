import os, sys, cv2
from utils import get_all_files_with_extension

def read_video(infile):
    cap = cv2.VideoCapture(infile)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frames = []
    tot_size = 0
    while 1:
        ret, frame = cap.read()
        if not ret:
            cap.release()
            tot_size /= (1024*1024)
            print(f'read {len(frames)} frames from {infile}, fps: {fps}, size (MB): {tot_size:.2f}')
            return frames, fps
        
        tot_size = sys.getsizeof(frame)
        frames.append(frame)


def save_video(outfile, frames, fps):
    size = (frames[0].shape[1], frames[0].shape[0])
    print('frame size:', size)
    # mp4 -> mp4v, avi -> MJPG, XVID
    vout = cv2.VideoWriter(outfile, cv2.VideoWriter_fourcc(*'XVID'), fps, size)
    for frame in frames:
        vout.write(frame)
    vout.release()


exit(0)  # looks like mp4 is larger than mov with cv2
error_files = []
files = get_all_files_with_extension('.mov')
for file in files:
    try:
        orig_size = os.path.getsize(file) / 1024 / 1024
        print(f'{file} size (MB): {orig_size:.2f}')
        continue
    
        frames, fps = read_video(file)

        i = file.rfind('.')
        outfile = file[0:i]+'.avi'
        save_video(outfile, frames, fps)
        new_size = os.path.getsize(outfile) / 1024 / 1024
        pct = 1.0 - new_size/orig_size
        
#        os.remove(file)
        print(f'{file} => {outfile}, Size (MB): {orig_size:.2f} => {new_size:.2f} (saved {pct*100.0:.2f}%)')
    except:
        print("Cannot process", file)
        import traceback
        traceback.print_exc()
        
        error_files.append(file)
    
#    break

print("Files with errors:")
for file in error_files:
    print('\t', file)

print(f'processed {len(files)} files')
