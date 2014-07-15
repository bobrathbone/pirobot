#!/usr/bin/env python
# Raspberry Pi Maplin Robot Arm
# $Id: test_switches.py,v 1.2 2013/08/29 06:18:29 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com

import os
import time
import RPi.GPIO as GPIO


# Switch definitions
GRIP_OPEN = 21
GRIP_CLOSE = 19
WRIST_UP = 18
WRIST_DOWN = 16
BASE_CLOCKWISE = 7
BASE_ANTI_CLOCKWISE = 8
SHOULDER_UP = 11
SHOULDER_DOWN = 10
ELBOW_UP = 13
ELBOW_DOWN = 12
LIGHT_ON = 24
LIGHT_OFF = 26

# Setup GPIO to to handle switches
def setupSwitches():
	GPIO.setmode(GPIO.BOARD)
	GPIO.setwarnings(False)
	GPIO.setup(BASE_CLOCKWISE,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
	GPIO.setup(BASE_ANTI_CLOCKWISE,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
	GPIO.setup(SHOULDER_UP,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
	GPIO.setup(SHOULDER_DOWN,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
	GPIO.setup(ELBOW_UP,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
	GPIO.setup(ELBOW_DOWN,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
	GPIO.setup(WRIST_UP,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
	GPIO.setup(WRIST_DOWN,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
	GPIO.setup(GRIP_OPEN,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
	GPIO.setup(GRIP_CLOSE,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
	#GPIO.setup(LIGHT_ON,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
	#GPIO.setup(LIGHT_OFF,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

	# Set up switch event processing
	t = 200
	GPIO.add_event_detect(BASE_CLOCKWISE,  GPIO.RISING, callback=switch_event, bouncetime=t)
	GPIO.add_event_detect(BASE_ANTI_CLOCKWISE, GPIO.RISING, callback=switch_event, bouncetime=t)
	GPIO.add_event_detect(SHOULDER_UP,   GPIO.RISING, callback=switch_event, bouncetime=t)
	GPIO.add_event_detect(SHOULDER_DOWN, GPIO.RISING, callback=switch_event, bouncetime=t)
	GPIO.add_event_detect(ELBOW_UP,   GPIO.RISING, callback=switch_event, bouncetime=t)
	GPIO.add_event_detect(ELBOW_DOWN, GPIO.RISING, callback=switch_event, bouncetime=t)
	GPIO.add_event_detect(WRIST_UP,   GPIO.RISING, callback=switch_event, bouncetime=t)
	GPIO.add_event_detect(WRIST_DOWN, GPIO.RISING, callback=switch_event, bouncetime=t)
	GPIO.add_event_detect(GRIP_OPEN,  GPIO.RISING, callback=switch_event, bouncetime=t)
	GPIO.add_event_detect(GRIP_CLOSE, GPIO.RISING, callback=switch_event, bouncetime=t)
	#GPIO.add_event_detect(LIGHT_ON,  GPIO.RISING, callback=switch_event, bouncetime=t)
	#GPIO.add_event_detect(LIGHT_OFF, GPIO.RISING, callback=switch_event, bouncetime=t)

	return

# Call back routine called by switch events
def switch_event(switch):
	print "Switch event " + str(switch)
	return



### Main routine ##
if __name__ == "__main__":

	setupSwitches()
	while True:
		time.sleep(0.1)


