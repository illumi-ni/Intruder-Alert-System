#*****trainPersonGroup.py*****#
import urllib, http.client, base64, json
import requests

group_id = 'members'
KEY = 'e2035d09c5264168abf90ba17e7994dd'

params = urllib.parse.urlencode({'personGroupId': group_id})
headers = {'Ocp-Apim-Subscription-Key': KEY}

conn = http.client.HTTPSConnection('southeastasia.api.cognitive.microsoft.com')
conn.request("POST", "/face/v1.0/persongroups/members/train?%s" % params, "{body}", headers)
response = conn.getresponse()

data = json.loads(response.read())
print(data) # if successful prints empty json body