#!/usr/bin/env python3
# Raspberry Pi Maplin Robot Arm
# $Id: robotd.py,v 1.17 2022/04/13 10:59:05 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# Credits
# -------
# The software to read the joystick to control the Maplin robotic arm 
# is based on software from www.mybigideas.co.uk (Author unknown)
#
# Run: sudo apt install python3-usb
# 
 

import os
import signal
import usb.core
import sys
import time
import termios
import tty
import RPi.GPIO as GPIO
from signal import SIGTERM

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame

# Class imports
from robot_daemon import Daemon
from log_class import Log
import pdb

log = Log()

_version = "1.0"

# Button to function mapping
buttonMap={
    3  : 'base-anti-clockwise',
    4  : 'base-clockwise',
    6  : 'elbow-up',
    5  : 'elbow-down',
    9  : 'wrist-up',
    10 : 'wrist-down',
    1  : 'grip-open',
    0  : 'grip-close',
    7 : 'light-on',
    8 : 'light-off',
    }

# Key to function
keyMap = {
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


# Maplin robot commands
commands={
    'base-anti-clockwise' : [0,1,0],
    'base-clockwise' : [0,2,0],
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

# Joystick axis settings
AXIS_HORIZONTAL = 0
AXIS_VERTICAL = 1

# Switch definitions (GPIO inputs)
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
LIGHT_ON = 22
LIGHT_OFF = 23


# How far to move the JoyStick before it has an effect (0.60 = 60%)
threshold = 0.60

# USB vendor and product IDs
usb_vendor_id=0x1267
usb_prod_id=0x000


#Daemon class
class Robot(Daemon):

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

    light_on = False    # Light on/off
        
    # Signal SIGTERM handler
    def signalHandler(self,sig,frame):
        msg = "Caught signal.SIGTERM: Exiting"
        if sig == signal.SIGTERM:
           log.message(msg, log.INFO)
           print(msg)
           try:
               os.remove(self.pidfile)
           except:
               pass
           sys.exit(0) 
     
    # ARM control related stuff
    def setCommand(self,axis_val):
        cmd = 0
        if axis_val > threshold:
            cmd = 1
        elif axis_val < -threshold:
            cmd = 2
        elif abs(axis_val) < threshold:
            cmd = 0
        return cmd

    def buildcommand(self,shoulc,basec,elbowc,wristc,gripc,lightc):
        arm = shoulc + elbowc +  wristc + gripc
        comm_bytes = (arm, basec, self.lightc)
        return comm_bytes

    # Main event handler
    def handleEvent(self,event):
        global commands
        if event.type is pygame.QUIT:
            log.message("Exiting robotd program", log.INFO)
            self.sendCommand(self.rctl,commands['stop'])
            pygame.joystick.quit()
            sys.exit(0)

        elif event.type == pygame.JOYAXISMOTION:
            self.handle_joystick(event)
        
        elif event.type is pygame.JOYBUTTONDOWN:
            log.message("JOYBUTTONDOWN " + str(event.button), log.DEBUG)
            cmd = self.getButtonCommand(event.button)
            log.message("Command " + cmd, log.DEBUG)

            if cmd == 'light-on':
                self.light_on = True
            elif cmd == 'light-off':
                self.light_on = False

            if cmd != '':
                self.execute(-1,cmd)

            log.message("A light = " + str(self.light_on), log.DEBUG)

        elif event.type is pygame.JOYBUTTONUP:
            button = event.button
            log.message("JOYBUTTONUP " + str(button), log.DEBUG)
            log.message("light_on " + str(self.light_on), log.DEBUG)
            if self.light_on:
                self.sendCommand(self.rctl,commands['light-on'])
            else:
                self.sendCommand(self.rctl,commands['stop'])

        # Work out what to send out to the robot
        if self.light_on:
            self.lightc = 1
        else:
            self.lightc = 0
        newcommand = self.buildcommand(self.shoulder_command,self.base_command, 
            self.elbow_command, self.wrist_command, self.grip_command,self.lightc)
                      
        # If the command has changed, send out the new one
        if newcommand != self.command:
            self.sendCommand(self.rctl, newcommand)
            self.command = newcommand

    # Handle the joystick event
    def handle_joystick(self,event):
        if event.axis == AXIS_VERTICAL:
            self.shoulder = event.value
        elif event.axis == AXIS_HORIZONTAL:
            self.base = event.value

        # setCommand returns 0, 1 or 2 so shoulder command is 0, 64 or 128
        self.shoulder_command = self.setCommand(self.shoulder)*64

        # setCommand returns 0, 1 or 2 so base command is 0, 1 or 2
        self.base_command = self.setCommand(self.base)

    # Get button command
    def getButtonCommand(self,button):
        try:
            cmd = buttonMap[button]
            return cmd
        except:
            return ""


    # Get the pid from the pidfile
    def status(self):
        try:
                pf = open(self.pidfile,'r')
                pid = int(pf.read().strip())
                pf.close()
        except IOError:
                pid = None

        if not pid:
                message = "robotd status: not running"
                log.message(message, log.INFO)
                print(message)
        else:
                message = "robotd running pid " + str(pid)
                log.message(message, log.INFO)
                print(message)
        return

    # Execute robot arm command
    def execute(self,t,cmd):
        global commands

        print("execute " + cmd)
        ##log.message("execute " + cmd, log.DEBUG)
        ##log.message("Light on =  " + str(self.light_on), log.DEBUG)

        try:
            if cmd == 'wait':
                    time.sleep(t)

            #Check that we can send commands to the arm
            elif self.checkComms():
                if cmd == 'light-on':
                    self.light_on = True
                if cmd == 'light-off':
                    self.light_on = False
                #pdb.set_trace()
                self.sendCommand(self.rctl, commands[cmd])
                if not "light" in cmd and t > 0:
                    time.sleep(t) #Wait
                    self.sendCommand(self.rctl,commands['stop'])
                    return True
                else:
                    return False

        except usb.core.USBError:
            log.message("USB communication error.", log.ERROR)
            return False

    # Checks that the arm is connected and we can talk to it
    def checkComms(self):
        #Object to talk to the robot
        self.rctl = usb.core.find(idVendor=usb_vendor_id, idProduct=usb_prod_id)
        try:
            if self.rctl != None:
                    return True
            else:
                    log.message("Couldn't talk to the robot arm.", log.ERROR)
                    return False

        except usb.core.USBError:
            log.message( "USB communication error.", log.ERROR)
            return False

    # Send a command to the Robot arm
    def sendCommand(self,rctl,cmd):
        connected = False
        log.message("sendCommand " + str(cmd), log.DEBUG)
        if self.checkComms():
            if self.light_on:
                l = list(cmd)   # Convert to a list
                l[2] = 1
                cmd = tuple(l)  # Convert back to tuple
            rctl.ctrl_transfer(0x40,6,0x100,0,cmd,1000) 
            connected = True
        return connected

    # Initialise the JoyStick
    def initJoyStick(self):
        # Wait for a joystick
        while pygame.joystick.get_count() == 0:
            count = pygame.joystick.get_count()
            log.message("Waiting for joystick count = " + str(count), log.DEBUG)
            time.sleep(10)
            pygame.joystick.quit()
            pygame.joystick.init()

        joystick = pygame.joystick.Joystick(0)
        joystick.init()
        return joystick

    # Setup GPIO to to handle switches
    def setupSwitches(self):
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
        GPIO.setup(LIGHT_ON,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(LIGHT_OFF,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        # Set up switch event processing
        t = 200
        GPIO.add_event_detect(BASE_CLOCKWISE,  GPIO.RISING, callback=self.switch_event, bouncetime=t)
        GPIO.add_event_detect(BASE_ANTI_CLOCKWISE, GPIO.RISING, callback=self.switch_event, bouncetime=t)
        GPIO.add_event_detect(SHOULDER_UP,   GPIO.RISING, callback=self.switch_event, bouncetime=t)
        GPIO.add_event_detect(SHOULDER_DOWN, GPIO.RISING, callback=self.switch_event, bouncetime=t)
        GPIO.add_event_detect(ELBOW_UP,   GPIO.RISING, callback=self.switch_event, bouncetime=t)
        GPIO.add_event_detect(ELBOW_DOWN, GPIO.RISING, callback=self.switch_event, bouncetime=t)
        GPIO.add_event_detect(WRIST_UP,   GPIO.RISING, callback=self.switch_event, bouncetime=t)
        GPIO.add_event_detect(WRIST_DOWN, GPIO.RISING, callback=self.switch_event, bouncetime=t)
        GPIO.add_event_detect(GRIP_OPEN,  GPIO.RISING, callback=self.switch_event, bouncetime=t)
        GPIO.add_event_detect(GRIP_CLOSE, GPIO.RISING, callback=self.switch_event, bouncetime=t)
        GPIO.add_event_detect(LIGHT_ON,  GPIO.RISING, callback=self.switch_event, bouncetime=t)
        GPIO.add_event_detect(LIGHT_OFF, GPIO.RISING, callback=self.switch_event, bouncetime=t)
        return

    # Call back routine called by switch events (GPIO event)
    def switch_event(self,switch):
        global commands
        log.message("Switch event " + str(switch), log.DEBUG)
        if switch == BASE_CLOCKWISE:
            cmd = commands['base-clockwise']
        elif switch == BASE_ANTI_CLOCKWISE:
            cmd = commands['base-anti-clockwise']
        elif switch == SHOULDER_UP:
            cmd = commands['shoulder-up']
        elif switch == SHOULDER_DOWN:
            cmd = commands['shoulder-down']
        elif switch == ELBOW_UP:
            cmd = commands['elbow-up']
        elif switch == ELBOW_DOWN:
            cmd = commands['elbow-down']
        elif switch == GRIP_CLOSE:
            cmd = commands['grip-close']
        elif switch == GRIP_OPEN:
            cmd = commands['grip-open']
        elif switch == WRIST_UP:
            cmd = commands['wrist-up']
        elif switch == WRIST_DOWN:
            cmd = commands['wrist-down']
        elif switch == LIGHT_ON:
            self.light_on = True
            cmd = commands['light-on']
        elif switch == LIGHT_OFF:
            self.light_on = False
            cmd = commands['light-off']
        else:
            log.message("Switch event not recognised " + str(switch), log.ERROR)

        if cmd != '':
            self.sendCommand(self.rctl, cmd)

            switchdown = GPIO.input(switch)
            while switchdown:
                time.sleep(0.1)
                switchdown = GPIO.input(switch)

            if self.light_on:
                self.sendCommand(self.rctl, commands['light-on'])
            else:
                self.sendCommand(self.rctl, commands['stop'])
        return

    def displayKeys(self):
        global keyMap
        print ("Key Command")
        print ("--- -------")
        for key in keyMap:
            print (key + "   " + keyMap[key])
        print  ("x   Exit program")
        print ("Enter command: ")
        return

    # Handle key events
    def key_event(self):
        self.displayKeys()
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        tty.setcbreak(sys.stdin)

        t = 0.1
        while True:
            key = sys.stdin.read(1)

            if key ==  'x':
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                sys.exit(0)

            else:
                try:
                    cmd = keyMap[key]
                    log.message("key " + key + " cmd = " + cmd, log.INFO)
                    self.execute(t,cmd)
                except:
                    self.displayKeys()
        return


    # Routine called by the start command
    def run(self):
        log.init("robot")
        signal.signal(signal.SIGTERM,self.signalHandler)
        log.message('Robot daemon running pid ' + str(os.getpid()), log.INFO)
        pygame.init()
        joystick = self.initJoyStick()
        self.setupSwitches()
        log.message('Initialized Joystick :' + joystick.get_name(),log.INFO)

        armFound = False
        while not armFound: 
            self.rctl = usb.core.find(idVendor=usb_vendor_id, idProduct=usb_prod_id)

            if self.rctl is None:
                log.message('Arm not found. Waiting', log.INFO)
                time.sleep(10)
            else:
                armFound = True

        #this arm should just have one configuration...
        self.rctl.set_configuration()

        log.message('Listening for commands', log.DEBUG)
        try:
            # Loop forwever
            while True:
                # Sleep so we don't eat up all the CPU time
                time.sleep(0.1)

                # read in events and process
                events = pygame.event.get()
                
                for event in events:
                    self.handleEvent(event) 
            
        except KeyboardInterrupt:
            joystick.quit()


### Main routine - handles command line arguments ###
if __name__ == "__main__":
    import pwd
    if pwd.getpwuid(os.geteuid()).pw_uid > 0:
        print ("This program must be run with sudo or root permissions!")
        sys.exit(1)

    daemon = Robot('/var/run/robotd.pid')
    robot = daemon
    log.init("robot")

    if len(sys.argv) >= 2:
        cmd = sys.argv[1]
        if len(sys.argv) == 2:
            # Daemon commands
            if cmd == 'start':
                daemon.start()
            elif cmd == 'stop':
                daemon.stop()
            elif cmd == 'nodaemon':
                daemon.nodaemon()
            elif cmd == 'restart':
                daemon.restart()
            elif cmd == 'status':
                daemon.status()
            elif cmd == 'version':
                print ("Version", _version)
            elif cmd == 'keyboard':
                robot.key_event()

        # Robot arm commands
        elif len(sys.argv) >= 3:
            message =  "Command " + cmd + " " + sys.argv[2]
            log.message(message, log.INFO)
            # Handle commands input file
            if cmd == 'execute':
                commandfile =  sys.argv[2]
                commandsfile = open(commandfile, "r")
                command_list = commandsfile.readlines()
                commandsfile.close()
                line = 1
                for command in command_list:
                    command = command.rstrip()
                    command = " ".join(command.split())
                    if len(command) < 1:
                        continue
                    log.message(command, log.INFO)
                    cmds = command.split(' ')
                    cmd = cmds[0]

                    try:
                        t = float(cmds[1])
                    except IndexError:
                        print ("Invalid or missing time: " + cmd + " in " + commandfile)
                        break

                    try:
                        # Check the command is valid
                        print ("Command " + str(line) + ": " + command)
                        if cmd != 'wait':
                            x = commands[cmd]
                        robot.execute(t, cmd)
                        line = line + 1

                    except KeyError:
                        print ("Invalid command: " + cmd + " in " + commandfile)
                        break
            else:
                message = "Unknown command: " + sys.argv[1]
                print (message)
                log.message(message, log.INFO)
                sys.exit(2)

            sys.exit(0)
    else:
        print ("Usage: %s start|stop|restart|status|version|nodaemon|<command>" % sys.argv[0])
        print ("Commands: keyboard - Use keyboard")
        print ("          execute <file>  - Execute commands in <file>")
        sys.exit(2)

# End of class
#set tabstop=4 shiftwidth=4 expandtab
#retab
