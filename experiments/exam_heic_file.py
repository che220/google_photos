import os
import logging
import pandas as pd
import cv2
import pyheif
from PIL import Image

pd.set_option('display.width', 5000)
pd.set_option('display.max_rows', 5000)
pd.set_option('display.max_colwidth', 5000)
pd.set_option('max_columns', 600)
pd.set_option('display.float_format', lambda x: '%.2f' % x)  # disable scientific notation for print

logging.basicConfig(format='%(asctime)s [%(name)s:%(lineno)d] [%(levelname)s] %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(os.path.basename(__file__))

infile = '/home/hui/TB/photos/2019-07/IMG_0001.heic'
heif_file = pyheif.read(infile)
im = Image.frombytes(heif_file.mode, heif_file.size, heif_file.data, "raw",
                     heif_file.mode, heif_file.stride,)
im.show()
exit(0)

cap = cv2.VideoCapture(infile)
cnts = 0
show_frame_info = True
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print('cannot read file. exit')
        break

    cnts += 1
    if show_frame_info:
        print('frame:', frame.shape)
        show_frame_info = False

#    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cv2.imshow('frame', frame)
    if cv2.waitKey(1) == ord('q'):
        break

print('total', cnts, 'frames')
cap.release()
cv2.destroyAllWindows()
