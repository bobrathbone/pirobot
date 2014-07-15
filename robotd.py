#!/usr/bin/env python
#
# Raspberry Pi Maplin Robot Arm
# $Id: robotd.py,v 1.8 2013/08/03 14:22:18 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
# 
# Robot commands
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
import signal
import sys
import time
import pygame
import RPi.GPIO as GPIO

#Use sudo pip install pyusb for usb.core
import usb.core, usb.util, time, sys


# Class imports
from robot_daemon import Daemon
from log_class import Log

# Switch definitions
GRIP_OPEN = 11
GRIP_CLOSE = 12
LIGHT_ON = 15
LIGHT_OFF = 16

log = Log()

# How far to move the JoyStick before it has an effect (0.60 = 60%)
threshold = 0.1

# Button to function mapping
buttonMap={
	3  : 'base-anti-clockwise',
	4  : 'base-clockwise',
	7  : 'shoulder-up',
	8  : 'shoulder-down',
	6  : 'elbow-up',
	5  : 'elbow-down',
	9  : 'wrist-up',
	10 : 'wrist-down',
	1  : 'grip-open',
	0  : 'grip-close',
	-1 : 'light-on',
	-1 : 'light-off',
	}

AXIS_HORIZONTAL = 0
AXIS_VERTICAL = 1

# Daemon class
class Robot(Daemon):

	moving = False	# Is arm in motion?
	# Robot Arm  defaults
	command = (0,0,0)
	lightc = 0 
	shoulder = 0 
	base = 0
	elbow = 0  
	wristup = 0
	wristdown = 0
	grip_open = 0
	grip_close = 0
	grip_command = 0 
	wrist_command = 0 
	shoulder_command = 0
	base_command = 0
	elbow_command = 0


	def run(self):
		log.init("robot")
		log.message('Robot daemon running pid ' + str(os.getpid()), log.INFO)
		pygame.init()
		self.initJoyStick()
		self.usb_vendor_id=0x1267
                self.usb_prod_id=0x000

                #Object to talk to the robot
                self.rctl = usb.core.find(idVendor=self.usb_vendor_id, idProduct=self.usb_prod_id)
                self.duration=1.0 # Duration (In seconds) for each action. Defaults to 1 second


		if self.checkComms():
			log.message('Connection to USB port OK ', log.INFO)
		else:
			sys.exit(1)

		self.execute(0, 'light-on')

		while True:
			self.checkSwitches()
			for event in pygame.event.get():
				self.handleEvent(event)
			time.sleep(0.5)

        def checkComms(self):
                '''Checks that the arm is connected and we can talk to it'''
		self.usb_vendor_id=0x1267
		self.usb_prod_id=0x000
		#Object to talk to the robot
		self.rctl = usb.core.find(idVendor=self.usb_vendor_id, idProduct=self.usb_prod_id)
                try:
                        if self.rctl != None:
                                return True
                        else:
                                log.message("Couldn't talk to the robot arm.", log.ERROR)
                                return False

                except usb.core.USBError:
                        log.message( "USB communication error.", log.ERROR)
                        return False


	def status(self):
		# Get the pid from the pidfile
		try:
			pf = file(self.pidfile,'r')
			pid = int(pf.read().strip())
			pf.close()
		except IOError:
			pid = None

		if not pid:
			message = "robotd status: not running"
	    		log.message(message, log.INFO)
			print message 
		else:
			message = "robotd running pid " + str(pid)
	    		log.message(message, log.INFO)
			print message 
		return

	# End of class overrides

	# Execute robot arm command
	def execute(self,t,cmd):
		self.commands={
			'base-anti-clockwise' : [0,1,1],
			'base-clockwise' : [0,2,1],
			'shoulder-up': [64,0,0],
			'shoulder-down': [128,0,0],
			'elbow-up': [16,0,0],
			'elbow-down': [32,0,0],
			'wrist-up': [4,0,0],
			'wrist-down': [8,0,0],
			'grip-open': [2,0,0],
			'grip-close': [1,0,0],
			'light-on': [0,0,1],
			'light-off': [0,0,0],
			'stop': [0,0,0],
			}

		try:
			if cmd == 'wait':
				time.sleep(t)

			#Check that we can send commands to the arm
			elif self.checkComms():
				log.message("Sending command " + cmd, log.DEBUG)
				self.rctl.ctrl_transfer(0x40,6,0x100,0,self.commands[cmd],1000) #Send command
				if not "light" in cmd and t > 0:
					time.sleep(t) #Wait
					self.stopArm()
				return True
			else:
				return False

		except usb.core.USBError:
			log.message("USB communication error.", log.ERROR)
			return False

	# Stop all robot arm actions
	def stopArm(self):

                if self.checkComms():
			log.message("STOP ", log.DEBUG)
                        self.rctl.ctrl_transfer(0x40,6,0x100,0,self.commands['stop'],1000) #Send stop command
                        return True
                else:
                        return False

	# Handle joystick event
	def handleEvent(self,event):

		if event.type is pygame.QUIT:
			log.message("Exiting robotd program", log.INFO)
			self.stopArm()
			pygame.joystick.quit()
			sys.exit(0)

		elif event.type is pygame.JOYAXISMOTION:
			self.handle_joystick(event)

		elif event.type is pygame.JOYBUTTONDOWN:
			button = event.button
			log.message("JOYBUTTONDOWN " + str(button), log.DEBUG)
			cmd = self.getButtonCommand(button)
			log.message("Command " + cmd, log.DEBUG)
			if cmd != '':
				self.execute(-1,cmd)

		elif event.type is pygame.JOYBUTTONUP:
			button = event.button
			log.message("JOYBUTTONUP " + str(button), log.DEBUG)
			self.stopArm()

		return

	# Build composite command
	def buildcommand(self,shoulc,basec,elbowc,wristc,gripc,lightc):
		byte1 = shoulc + elbowc +  wristc + gripc
		comm_bytes = (byte1, basec, lightc)
		print "Command = " + str(comm_bytes)
		return comm_bytes

	# ARM control related stuff 
	def setcommand(self,axis_val):
		if axis_val > threshold:
			return 1                
		elif axis_val < -threshold:
			return 2
		elif abs(axis_val) < threshold:
			return 0    
				

	# Handle joystick event
	def handle_joystick(self,event):

		if event.axis == AXIS_VERTICAL:
			self.shoulder = event.value
		elif event.axis == AXIS_HORIZONTAL:
			self.base = event.value

		# Are we opening or closing the gripper?
		if self.grip_open> threshold:
			self.grip_command = 1
		elif self.grip_close> threshold:
			self.grip_command = 2
		else:
			self.grip_command = 0


		# And the same for the wrist, are we moving up or down?
		if self.wristup > threshold:
			self.wrist_command = 1*4
		elif self.wristdown > threshold:
			self.wrist_command = 2*4
		else:
			self.wrist_command = 0
			self.shoulder_command = self.setcommand(self.shoulder)*64
			self.base_command = self.setcommand(self.base)
			self.elbow_command = self.setcommand(self.elbow)*16

		# Work out what to send out to the robot
		newcommand = self.buildcommand(self.shoulder_command,self.base_command,
				  self.elbow_command, self.wrist_command, self.grip_command,self.lightc)

		# If the command has changed, send out the new one
		log.message("Command new=" + str(newcommand) +  " old=" + str(self.command), log.DEBUG)
		if newcommand != self.command and not self.moving:
			#log.message("Command " + str(newcommand), log.INFO)
			self.rctl.ctrl_transfer(0x40, 6, 0x100, 0, newcommand, 1000)
			self.moving = True

		elif newcommand == (0,0,0) and self.moving:
			#log.message("Stop ", log.INFO)
			self.rctl.ctrl_transfer(0x40, 6, 0x100, 0, newcommand, 1000)
			self.moving = False
		return


	# Get button command
	def getButtonCommand(self,button):
		try:
			cmd = buttonMap[button]
			return cmd
		except:
			return ""

	# Initialise the JoyStick
	def initJoyStick(self):
		pygame.joystick.init()
		joystick = pygame.joystick.Joystick(0)
		joystick.init()
		return joystick

	# Setup GPIO to to handle switches
	def setupSwitches(self):
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(GRIP_OPEN,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
		GPIO.setup(GRIP_CLOSE,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
		GPIO.setup(LIGHT_ON,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
		GPIO.setup(LIGHT_OFF,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
		return

	# Check switches
	def checkSwitches(self):
		if GPIO.input(GRIP_OPEN):
			self.execute(0.1, 'grip-open')
		elif GPIO.input(GRIP_CLOSE):
			self.execute(0.1, 'grip-close')
		elif GPIO.input(LIGHT_ON):
			self.execute(0.1, 'light-on')
		elif GPIO.input(LIGHT_OFF):
			self.execute(0.1, 'light-off')
		return

### Main routine - handles command line arguments ###
if __name__ == "__main__":
	daemon = Robot('/var/run/robotd.pid')
	robot = daemon
	log.init("robot")
	robot.setupSwitches()

	if len(sys.argv) >= 2:
		# Daemon commands
		if 'start' == sys.argv[1]:
			daemon.start()
		elif 'stop' == sys.argv[1]:
			daemon.stop()
		elif 'restart' == sys.argv[1]:
			daemon.restart()
		elif 'status' == sys.argv[1]:
			daemon.status()
		elif 'version' == sys.argv[1]:
			print "Version  0.1" 

		# Robot arm commands
		elif len(sys.argv) >= 3:
			cmd = sys.argv[1]
			message =  "Command " + cmd + " " + sys.argv[2]
			log.message(message, log.INFO)

			# Handle commands input file
			if cmd == '-c':
				commandfile =  sys.argv[2]
				commandsfile = open(commandfile, "r")
				commands = commandsfile.readlines()
				commandsfile.close()
			 	for command in commands:
					command = command.rstrip()
					command = " ".join(command.split())
					log.message(command, log.INFO)
					cmds = command.split(' ')
					cmd = cmds[0]
					t = float(cmds[1])
					robot.execute(t, cmd)
						
			else:
				t = float(sys.argv[2])
				robot.execute(t, cmd)
		else:
			message = "Unknown command: " + sys.argv[1]
			print message
			log.message(message, log.INFO)
			sys.exit(2)
		sys.exit(0)
	else:
		print "usage: %s start|stop|restart|status|version|<command> <value>" % sys.argv[0]
		print "Commands: %s left|stop|restart|status|version" % sys.argv[0]
		sys.exit(2)

# End of script 

