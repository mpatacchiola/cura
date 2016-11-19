#!/usr/bin/env python3

import speech_recognition as sr
import os

from os import path
audioPath = "audiofiles"
folderPath = os.path.join(os.getcwd(), audioPath)
#folderPath = os.listdir(os.getcwd())

# use the audio file as the audio source
r = sr.Recognizer()
BING_KEY = "5e4addf308a64a9b8a4a86ccccc90781"

def convertVoiceToText_Google(r,audioFile):
        with sr.AudioFile(AUDIO_FILE) as source:
                audio = r.record(source) # read the entire audio file
                # recognize speech using Google Speech Recognition
                try:
                    # for testing purposes, we're just using the default API key
                    # to use another API key, use `r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
                    # instead of `r.recognize_google(audio)`
                        #list = r.recognize(audio,True)
                        print("Google Speech Recognition thinks you said " + r.recognize_google(audio))
                except sr.UnknownValueError:
                    print("Google Speech Recognition could not understand audio")
                except sr.RequestError as e:
                    print("Could not request results from Google Speech Recognition service; {0}".format(e))

        return	r.recognize_google(audio)

def convertVoiceToText_Bing(r,audioFile):
        with sr.AudioFile(AUDIO_FILE) as source:
                print("============")
                audio = r.record(source) # read the entire audio file
                print(audio)
                # recognize speech using Google Speech Recognition
                try:
                    # for testing purposes, we're just using the default API key
                    # to use another API key, use `r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
                    # instead of `r.recognize_google(audio)`
                        #list = r.recognize(audio,True)
                        print("Microsoft Bing Voice Recognition thinks you said " + r.recognize_bing(audio, key=BING_KEY))
                except sr.UnknownValueError:
                    print("Microsoft Bing Voice Recognition could not understand audio")
                except sr.RequestError as e:
                    print("Could not request results from Microsoft Bing Voice Recognition service; {0}".format(e))

        return	r.recognize_bing(audio)



for filename in os.listdir(folderPath):
	filename = filename;
	AUDIO_FILE = path.join(folderPath, filename)
	print(AUDIO_FILE)
	text = convertVoiceToText_Google(r,AUDIO_FILE)
	print(" Here is the audio text ::: ")
	print(text)

	## Call NLTK entity extraction
	

