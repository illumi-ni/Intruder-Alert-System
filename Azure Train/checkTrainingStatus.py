#*****checkTrainingStatus.py*****#
import urllib, http.client, base64, json

group_id = 'members'
KEY = 'e2035d09c5264168abf90ba17e7994dd'

headers = {'Ocp-Apim-Subscription-Key': KEY}
params = urllib.parse.urlencode({'personGroupId': group_id})
conn = http.client.HTTPSConnection('southeastasia.api.cognitive.microsoft.com')
conn.request("GET", "/face/v1.0/persongroups/members/training?%s" % params, "{body}", headers)
response = conn.getresponse()
data = json.loads(response.read())
print(data)
conn.close()