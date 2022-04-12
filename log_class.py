#!/usr/bin/env python3
#
# $Id: log_class.py,v 1.6 2022/04/11 08:51:26 bob Exp $
# Raspberry Pi Maplin Robot Arm
# Logging class
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com

import os
import logging
import pdb

class Log:

    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    DEBUG = logging.DEBUG

    RobotLibDir = "/var/lib/robotd"
    LogLevelFile = RobotLibDir + "/loglevel"
    LogDir = "/var/log"

    module = ''
    level = logging.INFO

    def __init__(self):
            return 

    # Initialise log file
    def init(self,module):
        self.module = module
        self.execCommand ("mkdir -p " + self.RobotLibDir )
        # Set up loglevel file
        if not os.path.isfile(self.LogLevelFile) or os.path.getsize(self.LogLevelFile) == 0:
            os.popen("echo INFO > " + self.LogLevelFile)
        self.level = self.getLevel()

    # Log message 
    def message(self,message,level):
        # Set up logging, level can be INFO, WARNING, ERROR, DEBUG
        # pdb.set_trace()
        ##assert len(self.module) > 0
        logrobot = self.LogDir + "/" + self.module
        self.execCommand ("sudo mkdir -p " +  logrobot)
        self.execCommand ("sudo chown pi:pi " + logrobot)
        logger = logging.getLogger('gipiod')
        hdlr = logging.FileHandler(self.LogDir + '/' + self.module + '/' + self.module + '.log')
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        logger.addHandler(hdlr)
        logger.setLevel(self.level)
        if level == logging.INFO:
            logger.info(message)
        if level == logging.WARNING:
            logger.warning(message)
        if level == logging.DEBUG:
            logger.debug(message)
        if level == logging.ERROR:
            logger.error(message)
        logger.removeHandler(hdlr)
        hdlr.close()

    # Temporary set log level
    def setLevel(self,level):
        self.level = level

    # Get the log level from the configuration file
    def getLevel(self):
        self.loglevel = logging.INFO
        if os.path.isfile(self.LogLevelFile):
            try:
                p = os.popen("cat " + self.LogLevelFile)
                strLogLevel = p.readline().rstrip('\n')
                if strLogLevel == "DEBUG":
                        self.loglevel = logging.DEBUG
                elif strLogLevel == "WARNING":
                        self.loglevel = logging.WARNING
                elif strLogLevel == "ERROR":
                        self.loglevel = logging.ERROR

            except ValueError:
                self.loglevel = logging.INFO

        return self.loglevel

    # Execute system command
    def execCommand(self,cmd):
        p = os.popen(cmd)
        return  p.readline().rstrip('\n')

# End of log class

#set tabstop=4 shiftwidth=4 expandtab
#retab
