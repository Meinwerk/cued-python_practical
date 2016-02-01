#########################################################
# CUED Python Statistical Spoken Dialogue System Software
#########################################################
#
# Copyright 2015-16  Cambridge University Engineering Department 
# Dialogue Systems Group
#
# Principal Authors:  Dongho Kim and David Vandyke
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#########################################################

'''
ContextLogger.py - wrapper for Python logging API
=================================================

Authors: Dongho Kim, David Vandyke  (Copyright CUED Dialogue Systems Group 2015)

**Basic Usage**:
    >>> import ContextLogger
    >>> ContextLogger.createLoggingHandlers()
    >>> logger = ContextLogger.getLogger('Name')
    
then within any script issue debug, info, warning and error messages, eg

    >>> logger.warning("String too long [%d]", 100)
    
issuing an error message generates ``ExceptionRaisedByLogger``.

Logger can if required be configured via a config section::

    [logging]
    screen_level=info
    file_level=debug
    file=logFileName.txt
    usecolor = False

Then pass config info to ``createLoggingHandlers``

    >>> ContextLogger.createLoggingHandlers(config)

************************

'''
__author__='donghokim, davidvandyke'

import contextlib, logging, argparse, inspect, copy, sys, traceback, time

# ----------------------------------------------
#   Configure the standard Python logging API
# ----------------------------------------------

msg_format = '%(levelname)-7s:: %(asctime)s: %(name)s %(message)s'
class NOcolors:
    """ASCII escape chars just print junk when dumping logger output to file. Can use the config setting usecolor.
    """
    HEADER = ''
    OKBLUE = ''
    OKGREEN = ''
    WARNING = ''
    FAIL = ''
    ENDC = ''
    BOLD = ''


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = "\033[1m"

class ConsoleFormatter(logging.Formatter):
    def __init__(self,*args, **kwargs) :
        self.color_choice = bcolors() if kwargs['colors'] in  [True, 'True'] else NOcolors()
        del kwargs['colors'] 

        kwargs['datefmt']='%H:%M:%S'
        logging.Formatter.__init__(self, msg_format, *args, **kwargs)

        self.mapping = {
            logging.WARNING: self.color_choice.WARNING,
            logging.ERROR: self.color_choice.FAIL,
            logging.INFO: self.color_choice.OKGREEN,
            logging.DEBUG: self.color_choice.OKBLUE
        }
        
    def format(self, record):
        record2 = copy.copy(record)
        if record.levelno in self.mapping:
            record2.levelname = self.mapping[record.levelno] + \
                                record.levelname.center(7) + self.color_choice.ENDC
        # get actual message:
        msg_split = record.msg.split('\n')
        msg = '\n'.join(msg_split[1:])
        record2.msg = msg_split[0] + '\n' + self.color_choice.BOLD + msg + self.color_choice.ENDC
        try:
            return super(ConsoleFormatter , self).format(record2)
        except TypeError:
            print 'except TypeError: in ContextLogger.ConsoleFormatter(). Known minor issue with message format of logger'

cl = {}             # current set of context loggers indexed by module name
module_level = {}   # logging level for each logger in cl
def createLoggingHandlers(config=None, screen_level = "INFO", \
                          log_file = None, file_level = "DEBUG", use_color = True):
    """ Create a top level logger and configure logging handlers

        :param config: a config structure as returned by the std ConfigParser |.|
        :param screen_level: (str) default screen logging level if no config |.|
        :param log_file: (str) default log file if no config |.|
        :param file_level: (str) default file logging level if no config
        :returns: None
            
        .. note::
            Valid logging levels are "DEBUG", "INFO", "WARNING", "ERROR"
                    
    """
    global cl
    global module_level
    
    top_logger = logging.getLogger('')
    top_logger.setLevel(logging.DEBUG)
    # levels for logging
    
    if config:
        if config.has_option("logging", "file") :
            log_file = config.get("logging", "file")
        if config.has_option("logging", "file_level") :
            file_level = config.get("logging", "file_level").upper()
        if config.has_option("logging", "screen_level") :
            screen_level = config.get("logging", "screen_level").upper()
        if config.has_option("logging", "usecolor"):
            use_color = config.get("logging", "usecolor")
        for option in config.options('logging'):
            if option not in ['usecolor','file', 'file_level', 'screen_level'] and option not in config.defaults():
                logger_name = option.lower()
                if logger_name in cl:
                    cl[logger_name].setLevel(config.get('logging', option))
                module_level[logger_name] = config.get('logging', option)
    

    # configure console output:
    """There was a problem with dumping logger output to file - print() statements and logger comments get separated. 
    StreamHandler now sends to sys.stdout 
    """
    ch = logging.StreamHandler(sys.stdout)  # NB: originally took no arguments
    ch.setLevel(getattr(logging, screen_level.upper()))
    ch.setFormatter(ConsoleFormatter(colors=use_color))
    # add the handlers to logger
    top_logger.addHandler(ch)
    #"""
    
    # configure file output:
    if log_file :
        # create file handler which logs even debug messages    
        formatter = logging.Formatter(msg_format,  datefmt='%H:%M:%S',)
        fh = logging.FileHandler(log_file, mode='w')
        fh.setLevel(getattr(logging, file_level.upper()))
        fh.setFormatter(formatter)
        top_logger.addHandler(fh)
    
# ----------------------------------------------
#   Interface to the standard Python logging API
# ----------------------------------------------

class ExceptionRaisedByLogger(Exception) :
    pass


class ContextLogger:
    """ Wrapper for Python logging class.
    
    """
    
    def __init__(self, module_name=None, *args):
        self.logger = logging.getLogger(module_name)
        self.stack = args
        self._log = []   
        sys.excepthook = self._exceptHook

    def setLevel(self, level):
        """ Set the logging level of this logger.

            :param level: (str) default screen logging level if no config
            :returns: None
        """
        self.logger.setLevel(getattr(logging, level.upper()))

    def _exceptHook(self, etype, value, tb) :
        if etype != ExceptionRaisedByLogger :
            msg = self._convertMsg("Uncaught exception: "+str(etype) + "( "+str(value)+" )\n")
            tb_msg = "".join( traceback.format_exception(etype, value, tb))
            tb_msg = "\n".join([(" "*10)+line for line in tb_msg.split("\n")])
            msg += tb_msg
            self.logger.error(msg)
        sys.__excepthook__(etype, value, tb)
        
    @contextlib.contextmanager
    def addContext(self, *args) :
        """ Create a nested named context for use in a ``with`` statement.
            
            :param args: list of one or more context names (str)
            :returns: ContextManager

            Example:
                >>> with mylogger.addContext("Session 1") :
                ...    mylogger.warning("Warn Message from Session 1")
        """
        n = len(self.stack)
        self.stack += args
        yield self.stack
        self.stack = self.stack[:n]
    
    @contextlib.contextmanager
    def addTimedContext(self, *args) :
        """ Create a timed nested named context for use in a ``with`` statement.
             
            :param args: list of one or more context names (str)
            :returns: ContextManager

            Example:
                >>> with mylogger.addContext("Session 1") :
                ...    Dostuff()
                
            On exit from the ``with`` statement, the elapsed time is logged.
        """

        t0 = time.time()
        n = len(self.stack)
        self.stack += args
        yield self.stack
        t1 = time.time()
        self.info("Timer %.4fs"%(t1-t0))
        self.stack = self.stack[:n]
    
    def _callLocString(self, ):
        inspected = inspect.getouterframes(inspect.currentframe())
        frame,filename,line_number,function_name,lines,index=inspected[min(3,len(inspected)-1)]
        filename = filename.split("/")[-1]
        return filename + ":" + function_name + ">" + str(line_number)
    
    
    def _stackString(self) :
        if len(self.stack) == 0:
            return ""
        return "(" + ", ".join(map(str, self.stack)) + "): "
    
    def _convertMsg(self, msg) :
        return self._callLocString() + ": " + self._stackString() + "\n          "+msg

    def debug(self,msg,*args,**kwargs):
        """ Log a DEBUG message.

            :param msg: (formatted-str) message string 
            :param args: args to formatted message string if any
            :returns: None
                
        """
        msg = self._convertMsg(msg)
        self.logger.debug(msg,*args,**kwargs)
    
    def info(self,msg,*args,**kwargs):
        """ Log an INFO message.

            :param msg: (formatted-str) message string 
            :param args: args to formatted message string if any
            :returns: None

        """
        msg = self._convertMsg(msg)
        self.logger.info(msg,*args,**kwargs)
    
    def warning(self,msg,*args,**kwargs):
        """ Log a WARNING message.

            :param msg: (formatted-str) message string 
            :param args: args to formatted message string if any
            :returns: None

        """
        msg = self._convertMsg(msg)
        self.logger.warning(msg,*args,**kwargs)
    
    def error(self,msg,*args,**kwargs):
        """ Log an ERROR message.

            :param msg: (formatted-str) message string 
            :param args: args to formatted message string if any
            :returns: None
               
            .. note::
                Issuing an error message also raises exception ``ExceptionRaisedByLogger``
        """
        msg0 = msg
        msg = self._convertMsg(msg)
        self.logger.error(msg,*args,**kwargs)
        raise ExceptionRaisedByLogger(msg0)
    
def getLogger(name):
    """ Retrieve or if necessary create a context logger with specified name.

        :param name: (str) name of logger to create or retrieve
        :returns: logger (ContextLogger.ContextLogger)
            
        .. note::
            Use **only** this function to create instances of the ContextLogger class
    """
    global cl
    name = name.lower()
    if name not in cl:
        cl[name] = ContextLogger(name)
        if name in module_level:
            cl[name].setLevel(module_level[name])

    # TODO - looking at problems when dumping simulate to file
    # colour tags are a mess. temp - testing
    # Delete? - this may not be an answer
    """
    import coloredlogs
    coloredlogs.install(level=logging.INFO)
    """

    return cl[name]
    
    
if __name__ == '__main__':
    # creates upside down traffic lights
    createLoggingHandlers()
    cl = ContextLogger(__name__)
    cl.info("starting test")
    with cl.addContext("session 1") :
        cl.warning("warning!")
        try :
            cl.error("error")
        except ExceptionRaisedByLogger :
            cl.info("ignoring the exception raised by the logger")
    with cl.addContext("session 2"):
        # try raising an exception
        x = {}
        print x["door"]
