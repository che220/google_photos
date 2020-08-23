import os
import pandas as pd
import numpy as np
import requests
import cv2
from photos import service

pd.set_option('display.width', 5000)
pd.set_option('display.max_rows', 5000)
#pd.set_option('display.max_colwidth', 5000)
pd.set_option('max_columns', 600)
pd.set_option('display.float_format', lambda x: '%.2f' % x)  # disable scientific notation for print


def show_img(img):
    print("image size:", img.shape)
    cv2.imshow("Image", img)
    cv2.waitKey(0)


def download_img(url):
    resp = requests.get(url)
    img = np.asarray(bytearray(resp.content), dtype="uint8")
    img = cv2.imdecode(img, cv2.IMREAD_UNCHANGED)
    return img


resp = service.mediaItems().list(pageSize=50).execute()
items = resp.get('mediaItems')

next_page_token = resp.get('nextPageToken', None)
cnt=0
while next_page_token:
    resp = service.mediaItems().list(pageSize=50, pageToken=next_page_token).execute()
    items += resp.get('mediaItems', None)
    next_page_token = resp.get('nextPageToken', None)
    cnt += 1
    if cnt > 1:
        break
    print(f'done batch {cnt}')

df = pd.DataFrame(items)
print(df.head(10))
print (df.shape)

id = df.id.iloc[0]
print(f'get {id} ...')
resp = service.mediaItems().get(mediaItemId=id).execute()
print(resp)

img = download_img(resp['baseUrl'])
show_img(img)
