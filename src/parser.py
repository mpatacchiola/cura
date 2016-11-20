from watson_developer_cloud import SpeechToTextV1
import json,os,sys
from configobj import ConfigObj
import nltk

class Parser:
	
	def __init__(self,config):
		self.config= config
		self.configObject = ConfigObj(config)
		
	def convertSpeechToText(self,audioFile):
		# Read IBM watson SpeechToText service username and password from config file
		username= self.configObject.get('ibm_speech_to_text_service_username')
		password =  self.configObject.get('ibm_speech_to_text_service_password')
		# Create SpeechToText service object
		stt = SpeechToTextV1(username=username, password=password)
		audio_file = open(audioFile, "rb")
		audio_data = json.dumps(stt.recognize(audio_file, content_type="audio/wav", model='en-US_NarrowbandModel', continuous=True), indent=2)
		print(audio_data)
		audio_text=""
                try:
		    audio_json_data = json.loads(audio_data)
		    print(" Here is the audio text :::")
		    if(len(audio_json_data["results"])!= 0 ):
		    	audio_text = audio_json_data["results"][0]["alternatives"][0]["transcript"]
			return(audio_text)
		    else:
			return(None)
		    
                except Exception,e:
                    print "Error was: ",e
		
		
	def extractNumbersFromText(self,audioText):
		num_dict = ('first','second','third','four','1','2','3','4','one','two','three','fourth','for','zero','0')
		numberList = list()
		words = nltk.word_tokenize(audioText)
		tokenized_words = [nltk.word_tokenize(word) for word in words]
		tagged_words = [nltk.pos_tag(word) for word in tokenized_words]
		for tag in tagged_words:
			tagged_word = tag[0]
			if tagged_word[1] == 'CD' or tagged_word[1] == 'RB' or tagged_word[1] == 'NN' or tagged_word[1] == 'JJ':
				if tagged_word[0] in num_dict:
					print(tagged_word[0])
					numberList.append(tagged_word[0])

		return(numberList)			
		

