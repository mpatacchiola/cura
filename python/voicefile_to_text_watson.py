from watson_developer_cloud import SpeechToTextV1
import json,os,sys
from configobj import ConfigObj

config = ConfigObj('config.ini')
username= config.get('username')
password =  config.get('password')


stt = SpeechToTextV1(username=username, password=password)

from os import path
audioPath = "audiofiles"
folderPath = os.path.join(os.getcwd(), audioPath)

for filename in os.listdir(folderPath):
	filename = filename;
	AUDIO_FILE = path.join(folderPath, filename)
	print(AUDIO_FILE)
	audio_file = open(AUDIO_FILE, "rb")
	audio_data = json.dumps(stt.recognize(audio_file, content_type="audio/wav"), indent=2)
	audio_json_data = json.loads(audio_data)
	print(" Here is the audio text ::: ")
	audio_text = audio_json_data["results"][0]["alternatives"][0]["transcript"]
	print(audio_text)
	sys.exit(0)
