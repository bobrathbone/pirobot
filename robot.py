#!/usr/bin/env python3
#
# Raspberry Pi Maplin Robot Arm
# $Id: robot.py,v 1.7 2022/04/11 08:51:26 bob Exp $
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
old_settings = None

# Register exit routine
def finish():
    global old_settings
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
    print ("Key Command")
    print ("--- -------")
    for cmd in commands:
        print (cmd + "   " + commands[cmd])
    print  ("x   Exit program")
    print
    return

### Main routine ###
if __name__ == "__main__":

    import pwd
    if pwd.getpwuid(os.geteuid()).pw_uid > 0:
        print ("This program must be run with sudo or root permissions!")
        sys.exit(1)

    displayKeys()
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
                cmd = commands[key]
                log.message(cmd, log.INFO)
                robot.execute(t,cmd)
            except Exception as e:
                print("robot.execute " + cmd + ": " +  str(e))
                sys.exit(1)
                #displayKeys()

# End of main

# set tabstop=4 shiftwidth=4 expandtab
# retab
