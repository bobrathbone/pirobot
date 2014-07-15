#!/usr/bin/env python
#
# Raspberry Pi Maplin Robot Arm
# $Id: robot.py,v 1.4 2013/08/15 11:43:23 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# Robot keyboard commands
#   <command> <time>
#   base-anti-clockwise - Rotates the base anticlockwise
#   base-clockwise - Rotates the base clockwise
#   shoulder-up - Raises the shoulder
#   shoulder-down - Lowers the shoulder
#   elbow-up - Raises the elbow
#   elbow-down - Lowers the elbow
#   wrist-up - Raises the wrist
#   wrist-down - Lowers the wrist
#   grip-open - Opens the grip
#   grip-close - Closes the grip
#   light-on - Turns on the LED in the grip
#   light-off - Turns the LED in the grip off
#   stop - Stops all movement of the arm
#   wait - Wait for <period>

import os
import sys
import tty
import termios
import time
import atexit
from robotd import Robot
from log_class import Log

log = Log()
robot = Robot('/var/run/robotd.pid')

# Register exit routine
def finish():
	robot.execute(0,'stop')
	# Restore stty settings
	termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
	log.message("Robot program stopped", log.INFO)
	print("Program stopped")

atexit.register(finish)

commands = {
	'a' : 'base-anti-clockwise',
	'z' : 'base-clockwise',
	'd' : 'shoulder-up',
	'c' : 'shoulder-down',
	'f' : 'elbow-up',
	'v' : 'elbow-down',
	'g' : 'wrist-up',
	'b' : 'wrist-down',
	'h' : 'grip-open',
	'n' : 'grip-close',
	'j' : 'light-on',
	'm' : 'light-off',
	'k' : 'stop',
	}

def displayKeys():
	log.init("robot")
	log.message("Robot program started", log.INFO)
	print "Key Command"
	print "--- -------"
	for cmd in commands:
		print cmd + "   " + commands[cmd]
	print  "x   Exit program"
	print
	return

### Main routine ###
if __name__ == "__main__":
        displayKeys()
	fd = sys.stdin.fileno()
	old_settings = termios.tcgetattr(fd)
	tty.setcbreak(sys.stdin)

	t = 0.1
	while True:
		key = sys.stdin.read(1)

		if key ==  'x': 
			sys.exit(0)

		else:
			try:
				cmd = commands[key]
				log.message(cmd, log.INFO)
				robot.execute(t,cmd)
			except:
				displayKeys()

# End of main

