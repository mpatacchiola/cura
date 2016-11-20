import sys  
import os
import time
import math
import random
import numpy as np
import ftplib
from PIL import Image
import cv2 
from datetime import datetime
import matplotlib.pyplot as plt
import pyaudio
import wave
import subprocess
from parser import Parser

#python -m pip install pyaudio
#sudo apt-get install python-pyaudio python3-pyaudio
import subprocess

#Importing my custom libraries
sys.path.insert(1, '../include')
sys.path.insert(1, "../include/pynaoqi-python2.7-2.1.3.3-linux64") #import this module for the nao.py module

#import pepper
from pepper import Puppet

#Pepper robot global variables
PEPPER_IP = "127.0.0.1"
PEPPER_PORT = 48289

#Image resolution
WIDTH = 1366
HEIGHT = 768

#Audio
AUDIO_TIME = '5'

def return_score(log_list):
    #'Trial': status_trial, 'Rule': status_current_rule, 
    #'PreviouRule': status_previous_rule, 'UserRule': status_user_rule
    total_trials = len(log_list)
    total_correct = 0
    total_perseveration_errors = 0
    for dictionary in log_list:
        if(dictionary['Rule'] == dictionary['UserRule']):
            total_correct += 1
        if(dictionary['Rule'] != dictionary['UserRule'] and dictionary['PreviouRule'] == dictionary['UserRule']):
            total_perseveration_errors += 1
    total_percentage_score = (total_correct / total_trials) * 100
    return total_correct, total_percentage_score, total_perseveration_errors

def return_deck():
    shape_patterns = []
    for i in range(1,5):
        z = np.zeros(4,int)
        z[0:i]=1
        shape_patterns.append(z.reshape((2,2)).tolist())
    color0 = [0,0,255]
    color1 = [0,255,0]
    color2 = [255,0,0]
    color3 = [0,255,255]
    shape_colors = [color0, color1, color2, color3]
    l = [0,1,2,3]
    deck = []
    for i in l:
        for j in l:
            for k in l:
                deck.append([i,j,k])
    new_deck = np.copy(deck)
    np.random.shuffle(new_deck)
    return new_deck, shape_patterns, shape_colors

def return_random_card_id(card1, card2, card3, card4):
    while(True):
        colour = np.random.randint(0, 5)
        shape = np.random.randint(0, 5)
        number = np.random.randint(0, 5)
        output_array = np.array([colour, shape, number])
        if(output_array != card1 and output_array!=card2 and output_array!=card3 and output_array!=card4):
            return np.array([colour, shpae, number])

def generate_hand():
    c = [0,1,2,3]
    s = [0,1,2,3]
    n = [0,1,2,3]
    np.random.shuffle(c)
    np.random.shuffle(s)
    np.random.shuffle(n)
    cards = []
    for i in range(4):
        cards.append([c[i],s[i],n[i]])
    return np.array(cards)

def generate_card(shape_num, shape_color = (0,0,255), shape_pattern = [[0,0],[0,1]], shape_scale = 2):
    '''
    shape_num: 0 (circle), 1 (rectangle), 2 (triangle) and 3 (cross).
    shape_color: (B,G,R)
    shape_pattern: [[0/1,0/1],[0/1,0/1]]
    '''
    x_dim,y_dim = 200,200
    shape = np.ones((x_dim,y_dim,3)) * 255
    cv2.rectangle(shape,(x_dim-2,y_dim-2),(1,1),(0,0,0),2)
    radius = int(10*shape_scale)
    thickness = int(2*shape_scale) # must be even
    color = shape_color
    pos_x,pos_y = 100,100
    pos_offsets = [(int(-x_dim/4),int(-y_dim/4)),
                   (int(+x_dim/4),int(-y_dim/4)),
                   (int(+x_dim/4),int(+y_dim/4)),
                   (int(-x_dim/4),int(+y_dim/4))]   
    for i,pos in enumerate([si for sj in shape_pattern for si in sj]):
        if pos:
            _pos_x = pos_x + pos_offsets[i][0]
            _pos_y = pos_y + pos_offsets[i][1]

            pts_t = np.array([[[_pos_x-radius,_pos_y+radius],
                                  [_pos_x+radius,_pos_y+radius],
                                  [_pos_x,_pos_y-radius],
                                  [_pos_x-radius,_pos_y+radius]]], dtype=np.int32)
            pts_c = np.array([[[_pos_x-thickness/2,_pos_y-radius],
                                  [_pos_x+thickness/2,_pos_y-radius],
                                  [_pos_x+thickness/2,_pos_y-thickness/2],
                                  [_pos_x+radius,_pos_y-thickness/2],
                                  [_pos_x+radius,_pos_y+thickness/2],
                                  [_pos_x+thickness/2,_pos_y+thickness/2],
                                  [_pos_x+thickness/2,_pos_y+radius],
                                  [_pos_x-thickness/2,_pos_y+radius],
                                  [_pos_x-thickness/2,_pos_y+thickness/2],
                                  [_pos_x-radius,_pos_y+thickness/2],
                                  [_pos_x-radius,_pos_y-thickness/2],
                                  [_pos_x-thickness/2,_pos_y-thickness/2]
                                 ]], dtype=np.int32)
            shape_args = [((_pos_x,_pos_y), radius, color, -1),
                          ((_pos_x-radius,_pos_y-radius),(_pos_x+radius,_pos_y+radius),color,-1),
                          (pts_t, color),
                          (pts_c, color)]
            shape_methods = [cv2.circle,cv2.rectangle,cv2.fillPoly,cv2.fillPoly]
            shape_methods[shape_num](shape,*shape_args[shape_num])    
    return shape

def main():
    #State machine internal variables
    TOTAL_TRIALS = 15
    status_trial = 1
    status_rules = ['colour', 'shape', 'number']
    status_current_rule = 'colour'
    status_previous_rule = 'colour'
    status_selected_card = 0 #the answer given from the user
    status_log = list()

    status_selected_card_array = np.zeros(3)
    status_correct_card_array = np.zeros(3)
    STATE_MACHINE = 0
    SIMULATOR = True

    while True:
        time.sleep(0.050) #50 msec sleep to evitate block

        #STATE-0 init
        if STATE_MACHINE == 0:
            print "[0] Init state..."
            my_puppet = Puppet(PEPPER_IP, PEPPER_PORT, SIMULATOR)
            my_puppet.wake_up()
            time.sleep(1)
            print "[0] Hello world!"
            my_puppet.say_something("Hello, I am Pepper. Let's play together.")
            time.sleep(1)
            print "[0] Enabling face tracking"
            my_puppet.enable_face_tracking(True)
            my_deck, my_shape_patterns, my_shape_colors = return_deck()
            my_unique_hand = generate_hand()
            print "[0] Creating the text to speach object"
            my_speech_to_text = Parser("./config.ini")
            STATE_MACHINE = 1 #switching to next state

        #STATE-1 Emotion checking
        if STATE_MACHINE == 1:

            status_emotions = "neutral" #TODO update this rule
            if(status_emotions == "happy" or status_emotions == "neutral"):
                my_puppet.say_something("I see that you are happy, it is time for your weekly test!")
            else:
                print "[1] Emotion Check: the value associated with the emotion variable: '" + str(status_emotions) + "' is not recognised"
            STATE_MACHINE = 2

        #STATE-2 Display
        if STATE_MACHINE == 2:
            print "[3] Display: Showing the image on screen"
            #Call the function to display the game on the screen
            if(SIMULATOR == True):
                #Creating a blank image
                img = np.zeros((HEIGHT , WIDTH, 3), np.uint8)
                img.fill(255)
                #Getting the center of the 4 figures
                center_a = (int((WIDTH / 8.) * 1), int(HEIGHT/4))
                center_b = (int((WIDTH / 8.) * 3), int(HEIGHT/4))
                center_c = (int((WIDTH / 8.) * 5), int(HEIGHT/4))
                center_d = (int((WIDTH / 8.) * 7), int(HEIGHT/4))
                img[center_a[1]-100:center_a[1]+100, center_a[0]-100:center_a[0]+100] = generate_card(my_unique_hand[0][0], my_shape_colors[my_unique_hand[0][1]], my_shape_patterns[my_unique_hand[0][2]])

                img[center_b[1]-100:center_b[1]+100, center_b[0]-100:center_b[0]+100] = generate_card(my_unique_hand[1][0], my_shape_colors[my_unique_hand[1][1]], my_shape_patterns[my_unique_hand[1][2]])

                img[center_c[1]-100:center_c[1]+100, center_c[0]-100:center_c[0]+100] = generate_card(my_unique_hand[2][0], my_shape_colors[my_unique_hand[2][1]], my_shape_patterns[my_unique_hand[2][2]])

                img[center_d[1]-100:center_d[1]+100, center_d[0]-100:center_d[0]+100] = generate_card(my_unique_hand[3][0], my_shape_colors[my_unique_hand[3][1]], my_shape_patterns[my_unique_hand[3][2]])


                print "[3] Generating the main card..."
                #Generating a random array with the correct sequence: 1=colour, 2=number, 3=shape
                status_main_card_array = np.array(my_deck[status_trial])
                #Getting the centre of the main card
                center_main = ( int((WIDTH / 2.)), int((HEIGHT/4) * 3))
                #Drawing the symbol
                img[center_main[1]-100:center_main[1]+100, center_main[0]-100:center_main[0]+100] = generate_card(my_deck[status_trial][0], my_shape_colors[my_deck[status_trial][1]], my_shape_patterns[my_deck[status_trial][2]])

               

                cv2.namedWindow("test", cv2.WND_PROP_FULLSCREEN)          
                cv2.setWindowProperty("test", cv2.WND_PROP_FULLSCREEN, cv2.cv.CV_WINDOW_FULLSCREEN)
                cv2.imshow("test",img)
                key=cv2.waitKey(1)
                time.sleep(3)                           
            STATE_MACHINE = 3

        #STATE-3 Invite the user to play
        if STATE_MACHINE == 3:
            print "[3] Play: inviting the user!"
            random_number = np.random.randint(0, 4)
            if(random_number == 0):
                my_puppet.say_something("Please make your choise!")
            elif(random_number == 1):
                my_puppet.say_something("Chose one of the card!")
            elif(random_number == 2):
                my_puppet.say_something("Which card do you want to choose?")
            elif(random_number == 3):
                my_puppet.say_something("Please make your choise!")
            else: 
                return
            STATE_MACHINE = 4

        #STATE-4 Record the audio to get the answer
        if STATE_MACHINE == 4:
            print "[4] Audio: starting audio recording"       
            try:
                #Record a file audio called test.wav for the specified seconds
                subprocess.call(['arecord', 'test.wav', '-d', AUDIO_TIME], shell=False)
            except Exception,e:
                print "[4]: error downloading the audio file"
                print "Error was: ",e

            #Sending the audio for analisys
            print "[4] Audio: analyzing the audio file!"
            my_text = my_speech_to_text.convertSpeechToText("./test.wav")
            if(my_text != None):
                print(my_speech_to_text.extractNumbersFromText(my_text))
            status_selected_card = 1  #TODO remeber to check the status here
            #If the feedback is good go to
            print "[4] Audio: giving the answer!"
            if(status_selected_card == -1):
                my_puppet.say_something("I did not understand your answer, can you repeat?")
                STATE_MACHINE = 4
            elif(status_selected_card == 0):
                my_puppet.say_something("Try to choose a card, if you don't know the answer pick a random one.")
                STATE_MACHINE = 4
            elif(status_selected_card == 1):
                status_selected_card_array = np.array(my_deck[0])
                my_puppet.say_something("You choose the first card.")
                STATE_MACHINE = 5
            elif(status_selected_card == 2):
                status_selected_card_array = np.array(my_deck[1])
                my_puppet.say_something("You choose the second card.")
                STATE_MACHINE = 5
            elif(status_selected_card == 3):
                status_selected_card_array = np.array(my_deck[2])
                my_puppet.say_something("You choose the third card.")
                STATE_MACHINE = 5
            elif(status_selected_card == 4):
                status_selected_card_array = np.array(my_deck[3])
                my_puppet.say_something("You choose the fourth card.")
                STATE_MACHINE = 5

        #STATE-5 Evaluating the human choice
        if STATE_MACHINE == 5:
            #The rule choosen by the guy is given by the zero value
            #in the array given by the difference between the selected_card and the main card
            result_card_array = status_selected_card_array - status_main_card_array
            result_card_array = np.absolute(result_card_array)
            status_user_rule = np.argmin(result_card_array)
            my_dict = {'Trial': status_trial, 'Rule': status_current_rule, 'PreviouRule': status_previous_rule, 'UserRule': status_user_rule }
            status_log.append(my_dict)
            if(status_trial % 10 == 0):
                if(status_current_rule == 'colour'): 
                    status_current_rule='shape'
                    status_previous_rule = 'colour'
                elif(status_current_rule == 'shape'): 
                    status_current_rule='number'
                    status_previous_rule = 'shape'
                elif(status_current_rule == 'number'): 
                    status_current_rule='colour'
                    status_previous_rule = 'number'
            #Switch state
            STATE_MACHINE = 6

        #STATE-6 Gives a feedback to the user (Correct / Not correct)
        if STATE_MACHINE == 6:          
            if(status_trial >= TOTAL_TRIALS):
                print("[6] The game is finished...")
                #All the correct answers are equal to zero
                #The wrong answer are different from zero
                #Turn the wrong values to 1 and find the score
                total_score, percentage_score, perseveration_errors = return_score(status_log)
                score_percentage = int((score / TOTAL_TRIALS) * 100)
                my_puppet.say_something("The game is finished, you gave the correct answer " + str(int(score_percentage)) + " percent of the time")
                my_puppet.say_something("You did a total of " + str(int(perseveration_errors)) + " perseveration errors")
                my_puppet.say_something("I'm sending the results of the test to your doctor for further analisys.")
                status_trial = 1
            else:
                if(status_current_rule==status_user_rule): my_puppet.say_something("Your choice is correct.")
                else: my_puppet.say_something("I am sorry, yur choice is not correct.")
       
                status_trial += 1
                STATE_MACHINE = 2

   
if __name__ == '__main__':  # if we're running file directly and not importing it
    main()  # run the main function
