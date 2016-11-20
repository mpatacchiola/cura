#!/usr/bin/env python


## @package pepper.py
#
# Massimiliano Patacchiola, Plymouth University 2016
#
# PREREQUISITES:
# naoqi SDK python, export the path in the terminal before using: export PYTHONPATH=${PYTHONPATH}:/path/to/pynaoqi-python2.7-2.1.3.3-linux64
# export PYTHONPATH=${PYTHONPATH}:/home/massimiliano/Desktop/PEPPER%20idm/pynaoqi-python2.7-2.1.3.3-linux64
# linux "play" mp3 player running in background with subprocess
# sudo apt-get install sox libsox-fmt-mp3
# acapela python text2speech US-Rod voice (with license)
# XML file with trial and experiment list (with exact format)
# minidom python XML parser

import sys
import time
import subprocess
import os

from naoqi import ALProxy

from sys import platform as _platform


class Puppet(object):

    def __init__(self, PEPPER_IP, PEPPER_PORT, SIMULATOR):
        """
        Class initialization
        """
        self._done = False
        self.SIMULATOR = SIMULATOR

        print("INIT: Getting robot state... ")
        self._al_motion_proxy = ALProxy("ALMotion", PEPPER_IP, int(PEPPER_PORT))
        print self._al_motion_proxy.getSummary()

        print("INIT: Getting the proxy objects... ")
        self._posture_proxy = ALProxy("ALRobotPosture", PEPPER_IP, int(PEPPER_PORT))

        print("INIT: Create a proxy to ALFaceDetection and ALTracker... ")
        try:
            self._face_proxy = ALProxy("ALFaceDetection", PEPPER_IP, int(PEPPER_PORT))
            self._tracker = ALProxy("ALTracker", PEPPER_IP, int(PEPPER_PORT))
        except Exception, e:
            print "INIT: Error when creating ALFaceDetection proxy:"
            print str(e)

        try:
            self._tts_proxy = ALProxy("ALTextToSpeech", PEPPER_IP, int(PEPPER_PORT))
        except Exception, e:
            print "INIT: Error when creating ALTextToSpeech proxy:"
            print str(e)

        try:
            self._audio_player_proxy = ALProxy("ALAudioPlayer", PEPPER_IP, int(PEPPER_PORT))
        except Exception, e:
            print "INIT: Error when creating ALAudioPlayer proxy:"
            print str(e)

        if self.SIMULATOR == False:
		self._video_proxy = ALProxy("ALVideoRecorder", PEPPER_IP, int(PEPPER_PORT))
                #Initialise a sound device
                self._audio_device_proxy = ALProxy("ALAudioDevice", PEPPER_IP, int(PEPPER_PORT))
        else:
		print("VIDEO: simulator mode, the video is not recorded. ")
		print("AUDIO: simulator mode, the audio is not recorded. ")    

        self._is_recording = False

    def start_audio_recording(self, file_name):
        ''' Record the audio from the robot microphones

        if in simulator mode it does not work
        '''
	if self.SIMULATOR == False:
		print("AUDIO: starting the audio record... ")
		complete_path = "/home/nao/" + str(file_name)
                channels = [0, 0, 1, 0] #[left, right, front, rear]
		self._audio_device_proxy.startMicrophonesRecording(complete_path, "wav", 16000, channels)
	else:
		print("AUDIO: simulator mode, the audio is not recorded") 

    def stop_audio_recording(self):
        ''' Stop recording the audio from the robot microphones

        if in simulator mode it does not work
        '''
	if self.SIMULATOR == False:
		print("AUDIO: starting the audio record... ")
		self._audio_device_proxy.stopMicrophonesRecording()
	else:
		print("AUDIO: simulator mode, the audio is not recorded")         

    ##
    # Play the PEPPER internal video
    # 
    #
    def play_video(self):
        # wake up the robot
	if self.SIMULATOR == False:
		print("VIDEO: starting the video record... ")
		# This records a 320*240 MJPG video at 10 fps.
		# Note MJPG can't be recorded with a framerate lower than 3 fps.
		date_string = strftime("%d%m%Y_%H%M%S", gmtime())
		self._video_proxy.setResolution(1)
		self._video_proxy.setFrameRate(10)
		self._video_proxy.setVideoFormat("MJPG")
		complete_path = "/home/PEPPER/recordings/cameras" + date_string
		#self._video_proxy.startVideoRecord(complete_path)
		self._video_proxy.startRecording("/home/PEPPER/recordings/cameras", date_string, True)
		self._is_recording = True
	else:
		print("VIDEO: simulator mode, the video is not recorded")

    ##
    # Stop the PEPPER internal video
    #
    def stop_video(self):
	if self.SIMULATOR == False:
                if self._video_proxy.isRecording() == True:
			print("VIDEO: stopping the video... ")
			videoInfo = self._video_proxy.stopRecording()
			self._is_recording = False
    ##
    # Robot wake up
    #
    def wake_up(self):
        # wake up the robot
        print("WAKE UP: waking up the robot... ")
	#self._al_motion_proxy.wakeUp()
	#self._al_motion_proxy.setAngles("HeadYaw", 0.0, HEAD_SPEED)
	#self._al_motion_proxy.setAngles("HeadPitch", 0.0, HEAD_SPEED)
        self._posture_proxy.goToPosture("Stand", 1)

    ##
    # Robot in rest mode
    #
    def rest(self):
        # the robot rest
        print("REST: the robot is going to sleep... ")
	self._al_motion_proxy.rest()

    ##
    # A player is called and an audio file is reproduced
    # @param file_path paath to the audio file to reproduce
    #
    #def say_something(self, file_path):
	#subprocess.Popen(["play","-q",filePath]) #using this method for the moment        
        # linux
        #if _platform == "linux" or _platform == "linux2":
            #print("PEPPER: playing the audio file on Linux... ")      
            #subprocess.Popen(["play","-q", file_path])
        # Windows...
        #elif _platform == "win32":
            #print("PEPPER: playing the audio file on windows... ")
            #print("PEPPER: the windows audio player is not called from here ")
            #abs_file_path = os.path.abspath(file_path)
            #os.startfile(abs_file_path) #It opens the audio file with the standard software associated

    ##
    # The robot say a sentence using its internal Voice proxy
    # @param sentence the string containing the sentence to say
    #
    def say_something(self, sentence, is_printing=True):
        self._tts_proxy.say(sentence)
        if(is_printing == True): print("PEPPER SAYS: " + str(sentence))

    ##
    # The robot plays an internal stored audio file
    # @param file_path the internal path to the audio file to reproduce
    # the root directory is: "/home/PEPPER"
    # @volume set the volume of the robot speakers (0.0 - 1.0)
    #
    def play_audio(self, file_path, volume=0.5):
        #check the volume
        if volume > 1.0:
            volume = 1.0
        if volume < 0.0:
            volume = 0.0
        try:
            #Loads a file
            path = str(file_path)
            fileId = self._audio_player_proxy.loadFile(path) #load file
            self._audio_player_proxy.setVolume(fileId, volume) #set volume
            time.sleep(0.1)
            self._audio_player_proxy.play(fileId)
        except Exception,e:
            print "PEPPER: error playing the audio file"
            print "Error was: ",e

    ##
    # It enables the face tracking component
    # @param state it can be true or false
    #
    def enable_face_tracking(self, state):

        try:                
            if state == True:
                print "PEPPER: enabling traking..."
                if (self._tracker.isActive() == True):
                    print "PEPPER: Is tracking now enabled on the robot?", self._tracker.isActive()
                    return
                faceWidth = 0.1
                self._tracker.registerTarget("Face", faceWidth) #Add target to track.   
                self._tracker.track("Face") # Start tracker.
                print "PEPPER: Is tracking now enabled on the robot?", self._tracker.isActive()
            elif state == False:
                print "PEPPER: disabling traking..."
                if (self._tracker.isActive() == False):
                    print "PEPPER: Is tracking now enabled on the robot?", self._tracker.isActive()
                    return 
                self._tracker.stopTracker() # Stop tracker.
                self._tracker.unregisterAllTargets()
                print "PEPPER: Is tracking now enabled on the robot?", self._tracker.isActive()

            #self._face_proxy.enableTracking(state)
        except Exception, e:
           print "Error: PEPPER face tracking error..."
           print str(e)
    ##
    # Pointing the screen with the right arm
    # @param state if True move the arm, if False set the arm in rest position
    # @param speed the speed of the movement (between 0 and 1)
    #
    def right_arm_pointing(self, state, speed):
        """
        Move the rigth arm
        """       	
        if state == True:
 	     self._al_motion_proxy.setAngles("RShoulderPitch", 1.0, speed) #arm goes up
             self._al_motion_proxy.setAngles("RWristYaw", -1.0, speed) #hand turn 
             time.sleep(0.3)
             self._al_motion_proxy.setAngles("RShoulderRoll", -0.5, speed) #arm move to the right
             time.sleep(0.1)
        elif state == False:
             self._al_motion_proxy.setAngles("RShoulderRoll", -0.2, speed) #this is the arm neutral position
             time.sleep(0.3)
             self._al_motion_proxy.setAngles("RWristYaw", 0.0, speed) #hand turn
  	     self._al_motion_proxy.setAngles("RShoulderPitch", 1.4, speed) #radians and speed  

    ##
    # Pointing the screen with the right arm
    # @param state if True move the arm, if False set the arm in rest position
    # @param speed the speed of the movement (between 0 and 1)
    #
    def left_arm_pointing(self, state, speed):
        """
        Move the left arm
        """       	
        if state == True:
 	     self._al_motion_proxy.setAngles("LShoulderPitch", 1.0, speed) #arm goes up
             self._al_motion_proxy.setAngles("LWristYaw", 1.0, speed) #hand turn             
             time.sleep(0.3)
             self._al_motion_proxy.setAngles("LShoulderRoll", 0.5, speed) #arm move to the left
             time.sleep(0.1)
        elif state == False:
             self._al_motion_proxy.setAngles("LShoulderRoll", 0.2, speed) #this is the arm neutral position
             time.sleep(0.3)
             self._al_motion_proxy.setAngles("LWristYaw", 0.0, speed) #hand turn
  	     self._al_motion_proxy.setAngles("LShoulderPitch", 1.4, speed) #arm goes down
          
    ##
    # Look to (only pitch)
    #
    # @param ANGLE pitch angle
    # @param HEAD_SPEED the speed of the movement (between 0 and 1)
    #
    def look_to(self, ANGLE, HEAD_SPEED):
        """
        Move the head looking to
        maximum angles: 29 / -38 (-2 +2 radians)
        maximum speed 1.0
        """       	
 	self._al_motion_proxy.setAngles("HeadPitch", ANGLE, HEAD_SPEED)
        self._al_motion_proxy.setAngles("HeadYaw", 0, HEAD_SPEED) #reset the yaw

    ##
    # Move the head saying yes
    #
    # @param ANGLE pitch angle
    # @param HEAD_SPEED the speed of the movement (between 0 and 1)
    #
    def say_yes(self, ANGLE, HEAD_SPEED, SLEEP_TIME):
        """
        Move the head saying YES
        """    
	print("YES: moving the head to say yes...")   	
 	#self._al_motion_proxy.setAngles("HeadPitch", HEAD_PITCH_BOTTOM, HEAD_SPEED)
	#time.sleep(SLEEP_TIME)
	self._al_motion_proxy.setAngles("HeadPitch", ANGLE, HEAD_SPEED)
	time.sleep(SLEEP_TIME)
 	self._al_motion_proxy.setAngles("HeadPitch", -ANGLE, HEAD_SPEED)
	time.sleep(SLEEP_TIME)
	self._al_motion_proxy.setAngles("HeadPitch", ANGLE, HEAD_SPEED)
	time.sleep(SLEEP_TIME)
	self._al_motion_proxy.setAngles("HeadYaw", 0.0, HEAD_SPEED)

    ##
    # Move the head saying no
    #
    # @param ANGLE pitch angle
    # @param HEAD_SPEED the speed of the movement (between 0 and 1)
    #
    def say_no(self, ANGLE, HEAD_SPEED, SLEEP_TIME):
        """
        Move the head saying NO
        """
	print("NO: moving the head to say no...")
 	self._al_motion_proxy.setAngles("HeadYaw", ANGLE, HEAD_SPEED)
	time.sleep(SLEEP_TIME)
	self._al_motion_proxy.setAngles("HeadYaw", -ANGLE, HEAD_SPEED)
	time.sleep(SLEEP_TIME)
 	self._al_motion_proxy.setAngles("HeadYaw", ANGLE, HEAD_SPEED)
	time.sleep(SLEEP_TIME)
	self._al_motion_proxy.setAngles("HeadYaw", -ANGLE, HEAD_SPEED)
	time.sleep(SLEEP_TIME)
	self._al_motion_proxy.setAngles("HeadYaw", 0.0, HEAD_SPEED)

    ##
    # Reset head angles to zero
    #
    # @param HEAD_SPEED the speed of the movement (between 0 and 1)
    #
    def set_neutral(self, HEAD_SPEED):
        """
        Sets the head back into a neutral pose
        """
	self._al_motion_proxy.setAngles("HeadYaw", 0.0, HEAD_SPEED)
	self._al_motion_proxy.setAngles("HeadPitch", 0.0, HEAD_SPEED)

    ##
    # Shutdown the robot
    #
    def shutdown(self):
	print("SHUTDOWN: unloading the mp3 file in the PEPPER...")

	print("SHUTDOWN: checking the video status...")
        if self._video_proxy.isRecording() == True:
		print("VIDEO: stopping the video record... ")
		videoInfo = self._video_proxy.stopRecording()
		self._is_recording = False

	print("SHUTDOWN: closing hands...")
	self._al_motion_proxy.closeHand("RHand");
	self._al_motion_proxy.closeHand("LHand");

	print("SHUTDOWN: moving to reset position...")
	self._al_motion_proxy.rest()

	print("SHUTDOWN: bye bye")



