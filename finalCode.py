import requests
from operator import itemgetter
from twilio.rest import Client
from picamera import PiCamera
import sys
import json
import os
import urllib, http.client, base64, json
import urllib.parse
import boto3
import datetime
import time
from espeak import espeak
import RPi.GPIO as GPIO

BaseDirectory = '/home/pi/Desktop/new' # directory where picamera photos are stored
KEY = 'e2035d09c5264168abf90ba17e7994dd' # authorization key for azure
account_sid = 'AC7cc2e2266f85a65aeeca493afc6da9a4' # twilio sid
auth_token = '12027af109b85547f46c1165280b7f78' # twilio authorization token
group_id = 'members' # name of personGroup
bucketName = 'members321' # aws s3 bucket name

#*****Raspberry Pi pin setup*****#
Pir= 23
servoPIN = 17

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(Pir, GPIO.IN)

GPIO.setup(servoPIN, GPIO.OUT)
pwm=GPIO.PWM(17, 50)
pwm.start(0)

espeak.set_voice("En")

#*****Camera Setup*****#
camera = PiCamera() # initiate camera

#*****FUNCTIONS*****#
def SetAngle(angle):
    duty = angle / 18 + 2
    GPIO.output(17, True)
    pwm.ChangeDutyCycle(duty)
    time.sleep(1)
    GPIO.output(17, False)
    pwm.ChangeDutyCycle(0)

# iterates through specified directory, detecting faces in .jpg files
def iter():
    print(directory)
    for fileName in os.listdir(directory):
        if fileName.endswith('.jpg'):
            filePath = os.path.join(directory, fileName) # joins directory path with filename to create file's full path
            fileList.append(filePath)
            detect(filePath)

# detects faces in images from previously stated directory using azure post request
def detect(img_url):
    headers = {'Content-Type': 'application/octet-stream', 'Ocp-Apim-Subscription-Key': KEY}
    body = open(img_url,'rb')

    params = urllib.parse.urlencode({'returnFaceId': 'true'})
    conn = http.client.HTTPSConnection('southeastasia.api.cognitive.microsoft.com')
    conn.request("POST", '/face/v1.0/detect?%s' % params, body, headers)
    response = conn.getresponse()
    photo_data = json.loads(response.read())

    if not photo_data: # if post is empty (meaning no face found)
        print('No face identified')
    else: # if face is found
        for face in photo_data: # for the faces identified in each photo
            faceIdList.append(str(face['faceId'])) # get faceId for use in identify

# Takes in list of faceIds and uses azure post request to match face to known faces
def identify(ids):
    if not faceIdList: # if list is empty, no faces found in photos
        result = [('n', .0), 'n'] # create result with 0 confidence
        return result # return result for use in main
    else: # else there is potential for a match
        headers = {'Content-Type': 'application/json', 'Ocp-Apim-Subscription-Key': KEY}
        params = urllib.parse.urlencode({'personGroupId': 'members'})
        body = "{'personGroupId':'members', 'faceIds':"+str(ids)+", 'confidenceThreshold': '.5'}"
        conn = http.client.HTTPSConnection('southeastasia.api.cognitive.microsoft.com')
        conn.request("POST", "/face/v1.0/identify?%s" % params, body, headers)
        response = conn.getresponse()

        data = json.loads(response.read())
        print(data) # turns response into index-able dictionary


        for resp in data:
            candidates = resp['candidates']
            if not candidates:
                return 0
            else: 
                for candidate in candidates: # for each candidate in the response
                    confidence = candidate['confidence'] # retrieve confidence
                    personId = str(candidate['personId']) # and personId
                    confidenceList.append((personId, confidence))
            conn.close()
            SortedconfidenceList = zip(confidenceList, fileList) # merge fileList and confidence list
            sortedConfidence = sorted(SortedconfidenceList, key=itemgetter(1)) # sort confidence list by confidence
            return sortedConfidence[-1] # returns tuple with highest confidence value (sorted from smallest to biggest)


# takes in person_id and retrieves known person's name with azure GET request
def getName(person_Id):
    headers = {'Ocp-Apim-Subscription-Key': KEY}
    params = urllib.parse.urlencode({'personGroupId': 'members', 'personId': person_Id})

    conn = http.client.HTTPSConnection('southeastasia.api.cognitive.microsoft.com')
    conn.request("GET", "/face/v1.0/persongroups/members/persons/"+person_Id+"?%s" % params, "{body}", headers)
    response = conn.getresponse()
    data = json.loads(response.read())
    name = data['name']
    conn.close()
    return name

# uses twilio rest api to send mms message, takes in message as body of text, and url of image
def twilio(message, imageLink):
    client = Client(account_sid, auth_token)
    message = client.messages.create(to='+9779825941070',
                                     from_='+16784987736',
                                     body = message,
                                     media_url=imageLink)
    print(message.sid)

# uses aws s3 to upload photos
def uploadPhoto(fName):
    s3=boto3.resource('s3')
    data = open(fName, 'rb')
    s3.Bucket(bucketName).put_object(Key=fName, Body=data, ContentType = 'image/jpeg')

    # makes uploaded image link public
    object_acl = s3.ObjectAcl(bucketName, fName)
    response = object_acl.put(ACL='bucket-owner-full-control')

    link = 'https://'+bucketName+'.s3.ap-south-1.amazonaws.com/'+fName
    return link

#*****Main*****#
count = 0
while True:
    # lists are refreshed for every incident of motion
    fileList = [] # list of filePaths that were passed through as images
    faceIdList = [] # list for face id's generated using api - detect
    confidenceList = [] # list of confidence values derived from api - identify
    
    i = GPIO.input(Pir)
    
    if GPIO.input(Pir) == False:
        print("No Intruders")
        
    elif i==1:
        count += 1 # count allows for a new directory to be made for each set of photos
        directory = BaseDirectory+str(count)+'/'
        print("Intruder Detected")
        os.mkdir(directory) # make new directory for photos to be uploaded to
#         print(count)
#         print(directory)
        
        for x in range(0,5):
            date = datetime.datetime.now().strftime('%m_%d_%Y_%M_%S_') # change file name for every photo
            camera.capture(directory + date +'.jpg')
            time.sleep(2) # take photo every second
        iter()
        result = identify(faceIdList)
        print(faceIdList)
        
        if result == 0:
            for files in fileList:
                    link = uploadPhoto(files) # upload all photos of incident for evidence
                    print(link)
                    twilio('Unknown intruder is in the Office.', link) # send message
            print('Unknown intruder detected')
            espeak.synth("Unknown intruder detected")
            time.sleep(30)
            
        else:
            if (result[0][1] > .5): # if confidence is greater than .7 get name of person
                twilio(getName(result[0][0])+' is in the Office.', uploadPhoto(result[1]))
                print(getName(result[0][0])+' is in the Office.')
                espeak.synth(getName(result[0][0]))
                
#               open the door if recognized
                SetAngle(120)
                time.sleep(5)
                SetAngle(30)
                
                time.sleep(60) # if recognized stop for 1 minute
        
            else:
                for files in fileList:
                    link = uploadPhoto(files) # upload all photos of incident for evidence
                    print(link)
                    espeak.synth("Motion detected")
                    twilio('Motion Detected in the Office.', link) # send message
                    time.sleep(30) # wait 30 seconds before looking for motion again
                
pwm.stop()
GPIO.cleanup()