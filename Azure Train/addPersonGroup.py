#*****addPersonGroup.py*****#
import requests
import urllib, http.client, base64

KEY = 'e2035d09c5264168abf90ba17e7994dd'

group_id = 'members'
body = '{"name": "Members"}'
params = urllib.parse.urlencode({'personGroupId': group_id})
headers = {'Content-Type': 'application/json', 'Ocp-Apim-Subscription-Key': KEY}

conn = http.client.HTTPSConnection('southeastasia.api.cognitive.microsoft.com')
conn.request("PUT", "/face/v1.0/persongroups/members?%s" % params, body, headers)
response = conn.getresponse()
data = response.read()
print(data)
conn.close()