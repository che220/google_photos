import json

a = "{'creationTime': '2021-09-04T21:41:55Z', 'width': '1440', 'height': '1080', 'photo': {}}"
a = a.replace("'", '"')
t = json.loads(a)['creationTime']
print(t[:10])
