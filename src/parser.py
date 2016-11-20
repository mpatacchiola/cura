from watson_developer_cloud import SpeechToTextV1
import json,os,sys,requests,operator,time
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
		    else:return(None)
		    
		except Exception as e:
                    print( "Error was: ",e)
		
		
	def extractNumbersFromText(self,audioText):
		num_dict = ('first','second','third','four','1','2','3','4','one','two','three','fourth','for','zero','0')
		numberList = list()
		words = nltk.word_tokenize(audioText)
		tokenized_words = [nltk.word_tokenize(word) for word in words]
		tagged_words = [nltk.pos_tag(word) for word in tokenized_words]
		for index,tag in enumerate(tagged_words):
			tagged_word = tagged_words[index][0]
			if tagged_word[1] == 'JJ':
				next_index= index+1
				if len(tagged_words) > next_index and tagged_words[next_index][0][0] == 'one':
						numberList.append(tagged_word[0])
				else:
					numberList.append(tagged_word[0])
				
			elif tagged_word[1] == 'CD' and tagged_words[index-1][0][1] == 'JJ':
				print("-- do nothing----")
			elif tagged_word[1] == 'CD' or tagged_word[1] == 'RB' or tagged_word[1] == 'NN' or tagged_word[1] == 'JJ':
				if tagged_word[0] in num_dict:
					numberList.append(tagged_word[0])

		return(numberList)			
		
		
	# to convert number text to integer number
	def text2int (self, textnum):
		numwords={}
		if not numwords:
			
				units = [
				"zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
				"nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
				"sixteen", "seventeen", "eighteen", "nineteen",
				]

				tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]

				scales = ["hundred", "thousand", "million", "billion", "trillion"]

				numwords["and"] = (1, 0)
				
				for idx, word in enumerate(units):  numwords[word] = (1, idx)
				for idx, word in enumerate(tens):       numwords[word] = (1, idx * 10)
				for idx, word in enumerate(scales): numwords[word] = (10 ** (idx * 3 or 2), 0)
				ordinal_words = {'first':1, 'second':2, 'third':3,'for':4,'forth':4, 'fifth':5, 'eighth':8, 'ninth':9, 'twelfth':12}
				ordinal_endings = [('ieth', 'y'), ('th', '')]
				
				textnum = textnum.replace('-', ' ')

				current = result = 0
				curstring = ""
				onnumber = False
				for word in textnum.split():
						if word in ordinal_words:
								scale, increment = (1, ordinal_words[word])
								current = current * scale + increment
								if scale > 100:
										result += current
										current = 0
								onnumber = True
						else:
								for ending, replacement in ordinal_endings:
										if word.endswith(ending):
												word = "%s%s" % (word[:-len(ending)], replacement)

								if word not in numwords:
										if onnumber:
												curstring += (result + current) + " "
										curstring += word + " "
										result = current = 0
										onnumber = False
								else:
										scale, increment = numwords[word]

										current = current * scale + increment
										if scale > 100:
												result += current
												current = 0
										onnumber = True

				if onnumber:
					curstring += repr(result + current)
				
				return int(curstring)

	
	# Function to identify emotions
	def identifyEmotionFromImage(self,imagePath):
		headers = dict()
		headers['Ocp-Apim-Subscription-Key'] = self.configObject.get('ms_emotion_api_key')
		headers['Content-Type'] = 'application/octet-stream'

		json = None
		params = None
		with open( imagePath, 'rb' ) as f:
			data = f.read()

		results = self.processRequest( json, data, headers, params )

		#json_result = json.loads(result)
		print(" Length of results: ")
		print(len(results))
		if(len(results) > 0):
			#print(results)
			highest_scored_emotion_list = list()
			for result in results: 
				emotion_dict = result["scores"]
				highest_scored_emotion = max(emotion_dict.items(), key=operator.itemgetter(1))[0]
				highest_scored_emotion_list.append(highest_scored_emotion)
			# Average emotion
			emotion_count_dict = dict((i, highest_scored_emotion_list.count(i)) for i in highest_scored_emotion_list)
			
			# Highest scored emotion
			highest_emotion = max(emotion_count_dict.items(), key=operator.itemgetter(1))[0]
			return(highest_scored_emotion)
		else:
			print(" No emotion identified")
			return(None)

	
	
	# function to process the request
	def processRequest(self,json, data, headers, params ):
		"""
		Helper function to process the request to Project Oxford

		Parameters:
		json: Used when processing images from its URL. See API Documentation
		data: Used when processing image read from disk. See API Documentation
		headers: Used to pass the key information and the data type request
		"""
		retries = 0
		result = None
		_maxNumRetries = 10
		while True:
			response = requests.request( 'post', self.configObject.get('ms_emotion_api_url'), json = json, data = data, headers = headers, params = params )
			if response.status_code == 429: 
				print( "Message: %s" % ( response.json()['error']['message'] ) )
				if retries <= _maxNumRetries: 
					time.sleep(1) 
					retries += 1
					continue
				else: 
					print( 'Error: failed after retrying!' )
					break

			elif response.status_code == 200 or response.status_code == 201:
				if 'content-length' in response.headers and int(response.headers['content-length']) == 0: 
					result = None 
				elif 'content-type' in response.headers and isinstance(response.headers['content-type'], str): 
					if 'application/json' in response.headers['content-type'].lower(): 
						result = response.json() if response.content else None 
					elif 'image' in response.headers['content-type'].lower(): 
						result = response.content
			else:
				print( "Error code: %d" % ( response.status_code ) )
				print( "Message: %s" % ( response.json()['error']['message'] ) )
			break
		return result

	
# Condition to check the digi
my_parser = Parser("../config/config.ini")			

# Load raw image file into memory
pathToFileInDisk = 'C:\\Users\\357677\\Documents\\Projects\\Hackathon\\images\\img2.jpg'

with open( pathToFileInDisk, 'rb' ) as f:
    data = f.read()

print(my_parser.identifyEmotionFromImage(pathToFileInDisk))
#numbers = my_parser.extractNumbersFromText("the number	one ")
#print("--- Length of number list---------")

#print(numbers)
#if(len(numbers) == 0):
#	outputDigit = -1
#elif len(numbers) == 1:
	
#	outputDigit = my_parser.text2int(numbers[0])
#	print(my_parser.text2int(numbers[0]))
#else:
#	outputDigit = 0;
#print("outputDigit :",outputDigit)



