import os
import pandas as pd
from photos import service

pd.set_option('display.width', 5000)
pd.set_option('display.max_rows', 5000)
pd.set_option('display.max_colwidth', 5000)
pd.set_option('max_columns', 600)
pd.set_option('display.float_format', lambda x: '%.2f' % x)  # disable scientific notation for print

exit(0)

resp = service.albums().list(pageSize=50, excludeNonAppCreatedData=False).execute()
print(resp)
print(resp.keys())

album_list = resp.get('albums')
print(album_list)

next_page_token = resp.get('nextPageToken', None)
print(next_page_token)

while next_page_token:
    resp = service.albums().list(pageSize=50, pageToken=next_page_token, excludeNonAppCreatedData=False)
    album_list.append(resp.get('albums', None))
    next_page_token = resp.get('nextPageToken', None)

df_albums = pd.DataFrame(album_list)
print(df_albums.id)

id = df_albums.id.iloc[0]
resp = service.albums().get(albumId=id).execute()
print(resp)

