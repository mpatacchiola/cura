import sys  
import os
import time
import math
import random
import numpy as np
import cv2 
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
PEPPER_IP = "192.168.1.100"
PEPPER_PORT = 9559
TOTAL_TRIALS = 5
SIMULATOR = True

#Image resolution
WIDTH = 1366
HEIGHT = 768

#Audio
AUDIO_TIME = '4'

def return_score(log_list, is_printing=True):
    #'Trial': status_trial, 'Rule': status_current_rule, 
    #'PreviouRule': status_previous_rule, 'UserRule': status_user_rule
    total_trials = len(log_list)
    total_correct = 0.0
    total_perseveration_errors = 0.0
    for dictionary in log_list:
        if(is_printing==True): print(dictionary)
        if(dictionary['Rule'] == dictionary['UserRule']):
            if(is_printing==True): print("Match: Rule="+dictionary['Rule'] + " UserRule=" + dictionary['UserRule'] )
            total_correct += 1
        else:
            if(dictionary['PreviouRule'] == dictionary['UserRule']): total_perseveration_errors += 1
    total_percentage_score = (total_correct / total_trials) * 100.0
    return int(total_correct), int(total_percentage_score), int(total_perseveration_errors)

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

    status_trial = 1
    status_rules = ['colour', 'shape', 'number']
    status_current_rule = 'colour'
    status_previous_rule = 'colour'
    status_selected_card = 0 #the answer given from the user
    status_log = list()
    STATE_MACHINE = 0
    status_selected_card_array = np.zeros(3)
    status_correct_card_array = np.zeros(3)

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
            my_speech_to_text = Parser("../config/config.ini")
            print "[0] Setting up the OpenCV variables"
            cv2.namedWindow("test", cv2.WND_PROP_FULLSCREEN)          
            cv2.setWindowProperty("test", cv2.WND_PROP_FULLSCREEN, cv2.cv.CV_WINDOW_FULLSCREEN)
            print("")
            print "[Q]uick start: jump the introduction."
            print "[S]tart: standard start, with robot introduction."
            print "[E]xit: close the window."
            STATE_MACHINE = 1 #switching to next state
            print("")
e
        #STATE-1 Emotion checking and waiting for input
        if STATE_MACHINE == 1:
            if cv2.waitKey(33) == ord('s'):
                my_puppet.say_something("Welcome! My name is Pepper and today I'm here as part of the project cure. Today we will play a game. Actually this is not a game.")
                my_puppet.say_something("This is the Wisconsin card sorting test. This test is a neuro psychological test which is widely used by clinical psychologists to test patients with brain injuries and mental illnesses.")
                my_puppet.say_something("Your role is to find the right match for the card that I will show you on the screen.")
                my_puppet.say_something("The cards could be matched by number, colour or shape of the symbols.")
                my_puppet.say_something("Choose the card you think is the best match. Let's start!")
                print "[1] Switching to the next state..."
                STATE_MACHINE = 2
            if cv2.waitKey(33) == ord('e'):
                print "[1] Closing the window..."
                return
            if cv2.waitKey(33) == ord('q'):
                print "[1] Quick start!"
                STATE_MACHINE = 2

        #STATE-2 Display
        if STATE_MACHINE == 2:
            print("")
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
                img[center_a[1]-100:center_a[1]+100, center_a[0]-100:center_a[0]+100] = generate_card(my_unique_hand[0][1], my_shape_colors[my_unique_hand[0][0]], my_shape_patterns[my_unique_hand[0][2]])
                cv2.putText(img, "1", (center_a[0]-20, center_a[1]+160), cv2.cv.CV_FONT_HERSHEY_SIMPLEX, 1.5, (0,0,0), 3)

                img[center_b[1]-100:center_b[1]+100, center_b[0]-100:center_b[0]+100] = generate_card(my_unique_hand[1][1], my_shape_colors[my_unique_hand[1][0]], my_shape_patterns[my_unique_hand[1][2]])
                cv2.putText(img, "2", (center_b[0]-20, center_b[1]+160), cv2.cv.CV_FONT_HERSHEY_SIMPLEX, 1.5, (0,0,0), 3)

                img[center_c[1]-100:center_c[1]+100, center_c[0]-100:center_c[0]+100] = generate_card(my_unique_hand[2][1], my_shape_colors[my_unique_hand[2][0]], my_shape_patterns[my_unique_hand[2][2]])
                cv2.putText(img, "3", (center_c[0]-20, center_c[1]+160), cv2.cv.CV_FONT_HERSHEY_SIMPLEX, 1.5, (0,0,0), 3)

                img[center_d[1]-100:center_d[1]+100, center_d[0]-100:center_d[0]+100] = generate_card(my_unique_hand[3][1], my_shape_colors[my_unique_hand[3][0]], my_shape_patterns[my_unique_hand[3][2]])
                cv2.putText(img, "4", (center_d[0]-20, center_d[1]+160), cv2.cv.CV_FONT_HERSHEY_SIMPLEX, 1.5, (0,0,0), 3)

                print "[3] Generating the main card..."
                #Generating a random array with the correct sequence: 1=colour, 2=number, 3=shape
                #status_main_card_array = np.array(my_deck[status_trial])
                #Getting the centre of the main card
                center_main = ( int((WIDTH / 2.)), int((HEIGHT/4) * 3))
                #Drawing the symbol
                img[center_main[1]-100:center_main[1]+100, center_main[0]-100:center_main[0]+100] = generate_card(my_deck[status_trial][0], my_shape_colors[my_deck[status_trial][1]], my_shape_patterns[my_deck[status_trial][2]])

                #Showing the image
                cv2.imshow("test",img)
                key=cv2.waitKey(1)

                time.sleep(2)                           
            STATE_MACHINE = 3

        #STATE-3 Invite the user to play
        if STATE_MACHINE == 3:
            print("")
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
            print("")
            print "[4] Audio: starting audio recording" 
            listening_img = cv2.imread("./listening.png")
            listening_img = cv2.resize(listening_img, (100, 100)) 
            img[HEIGHT-200:HEIGHT-100, WIDTH-200:WIDTH-100] = listening_img
            #cv2.namedWindow("test", cv2.WND_PROP_FULLSCREEN)          
            #cv2.setWindowProperty("test", cv2.WND_PROP_FULLSCREEN, cv2.cv.CV_WINDOW_FULLSCREEN)
            cv2.imshow("test",img)
            key=cv2.waitKey(1)
      
            try:
                #Record a file audio called test.wav for the specified seconds
                subprocess.call(['arecord', 'test.wav', '-d', AUDIO_TIME], shell=False)
            except Exception,e:
                print "[4]: error downloading the audio file"
                print "Error was: ",e

            #Clean the listening symbol
            print "[4] Displaying the clean image (no listening symbol)" 
            no_listening_img = np.ones((100, 100, 3)) * 255
            img[HEIGHT-200:HEIGHT-100, WIDTH-200:WIDTH-100] = no_listening_img
            cv2.imshow("test",img)
            key=cv2.waitKey(1)

            #Sending the audio for analisys
            print "[4] Audio: analyzing the audio file!"
            try:
                my_text = my_speech_to_text.convertSpeechToText("./test.wav")
                number_list = list()
                if(my_text != None):
                    print("my_text: ")
		    print(my_text)
                    number_list = my_speech_to_text.extractNumbersFromText(my_text)
	    except Exception as e:
                print( "Error was: ",e)

	    print(" Number List :")
	    print(number_list)
	    print(len(number_list))
            if(len(number_list) == 0): 
                status_selected_card = -1
            elif(len(number_list)==1): 
                number_answer = my_speech_to_text.text2int(number_list[0])
                print("number_answer :" )
                print(number_answer)
                status_selected_card = number_answer
            else:
                status_selected_card = 0
            print("[4] The answer given is: " + str(status_selected_card))


            print "[4] Audio: giving the answer!"
            if(status_selected_card == -1):
                random_number = np.random.randint(0, 4)
                if(random_number == 0):
                    my_puppet.say_something("I did not understand your answer, can you repeat?")
                if(random_number == 1):
                    my_puppet.say_something("Did you say something? Please repeat.")
                if(random_number == 2):
                    my_puppet.say_something("What did you say? Can you repeat again please?")
                if(random_number == 3):
                    my_puppet.say_something("Repeat again when the listening symbol appears in the bottom right corner.")
                STATE_MACHINE = 4
                time.sleep(2)
            elif(status_selected_card == 0):
                my_puppet.say_something("Try to choose a single card, if you don't know the answer pick a random one.")
                STATE_MACHINE = 4
                time.sleep(2)
            elif(status_selected_card == 1):
                status_selected_card_array = np.array(my_unique_hand[0])
                my_puppet.say_something("You choose the first card.")
                STATE_MACHINE = 5
                time.sleep(1)
            elif(status_selected_card == 2):
                status_selected_card_array = np.array(my_unique_hand[1])
                my_puppet.say_something("You choose the second card.")
                STATE_MACHINE = 5
                time.sleep(1)
            elif(status_selected_card == 3):
                status_selected_card_array = np.array(my_unique_hand[2])
                my_puppet.say_something("You choose the third card.")
                STATE_MACHINE = 5
                time.sleep(1)
            elif(status_selected_card == 4):
                status_selected_card_array = np.array(my_unique_hand[3])
                my_puppet.say_something("You choose the fourth card.")
                STATE_MACHINE = 5
                time.sleep(1)
            else:
                print("The value of status_selected_card is not correct")
                STATE_MACHINE = 5
                time.sleep(1)               
            #Sleep to have a better visualization of the
            #clean background without listening
            time.sleep(1)

        #STATE-5 Evaluating the human choice
        if STATE_MACHINE == 5:
            print("")
            print("[5] Evaluating the human choice...")
            #The rule choosen by the guy is given by the zero value
            #in the array given by the difference between the selected_card and the main card
            #result_card_array = status_selected_card_array - status_main_card_array
            #result_card_array = np.absolute(result_card_array)
            #status_user_rule = status_rules[np.argmin(result_card_array)]

            if(status_current_rule=='colour' and status_selected_card_array[0] == my_deck[status_trial][0]): status_user_rule='colour'
            elif(status_current_rule=='shape' and status_selected_card_array[1] == my_deck[status_trial][1]): status_user_rule='shape'
            elif(status_current_rule=='number' and status_selected_card_array[2] == my_deck[status_trial][2]): status_user_rule='number'
            else:
                result_card_array = status_selected_card_array - my_deck[status_trial]
                result_card_array = np.absolute(result_card_array)
                if(np.amin(result_card_array) == 0): 
                    status_user_rule = status_rules[np.argmin(result_card_array)]
                else:
                    status_user_rule = "None"

            my_dict = {'Trial': status_trial, 'Rule': status_current_rule, 'PreviouRule': status_previous_rule, 'UserRule': status_user_rule }
            status_log.append(my_dict)
            if(status_trial % 10 == 0):
                print("[5] Switching to a new rule...")
                if(status_current_rule == 'colour'): 
                    status_current_rule='shape'
                    status_previous_rule = 'colour'
                elif(status_current_rule == 'shape'): 
                    status_current_rule='number'
                    status_previous_rule = 'shape'
                elif(status_current_rule == 'number'): 
                    status_current_rule='colour'
                    status_previous_rule = 'number'
            #Printing generic info
            print("Trial: " + str(status_trial))
            print("Selected Card Array: " + str(status_selected_card_array))
            print("Main Card Array: " + str(my_deck[status_trial]))
            print("Current Rule: " + str(status_current_rule))
            print("Previous Rule: " + str(status_previous_rule))
            print("User Rule: " + str(status_user_rule))
            #Switch state
            STATE_MACHINE = 6

        #STATE-6 Gives a feedback to the user (Correct / Not correct)
        if STATE_MACHINE == 6:          
            if(status_trial >= TOTAL_TRIALS):
                print("")
                print("[6] The game is finished...")
                #All the correct answers are equal to zero
                #The wrong answer are different from zero
                #Turn the wrong values to 1 and find the score
                total_score, percentage_score, perseveration_errors = return_score(status_log)
                my_puppet.say_something("The game is finished, you gave the correct answer " + str(int(percentage_score)) + " percent of the time")
                my_puppet.say_something("You did a total of " + str(perseveration_errors) + " perseveration errors")
                my_puppet.say_something("I'm sending the results of the test to your doctor for further analisys.")
                print("[6] Press 'S' to start a new game...")
                status_trial = 1
                STATE_MACHINE = 1
            else:
                if(status_current_rule==status_user_rule):
                    random_number = np.random.randint(0, 3)
                    if(random_number == 0):
                        my_puppet.say_something("Your choice is correct.")
                    if(random_number == 1):
                        my_puppet.say_something("Well done! Your answer is correct.")
                    if(random_number == 2):
                        my_puppet.say_something("You are right, that's the right answer.")
                else:
                    random_number = np.random.randint(0, 3)
                    if(random_number == 0):
                        my_puppet.say_something("I am sorry, yur choice is not correct.")
                    elif(random_number == 1):
                        my_puppet.say_something("I am sorry, the answer is not correct. You can do better the next trial.")
                    elif(random_number == 2):
                        my_puppet.say_something("This time the answer is not correct. Try again!")
                status_trial += 1
                STATE_MACHINE = 2

   
if __name__ == '__main__':  # if we're running file directly and not importing it
    main()  # run the main function

