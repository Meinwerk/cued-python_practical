'''
Settings.py - global domain/config variables 
====================================================

Author: Dongho Kim, David Vandyke  (Copyright CUED Dialogue Systems Group 2015)

Globals::
  
    config:       python ConfigParser.ConfigParser() object
    random:       numpy.random.RandomState() random number generator

.. seealso:: CUED Imports/Dependencies: 

    import :class:`ContextLogger`

************************

'''
__author__ = "donghokim, davidvandyke"
import ConfigParser
import json
import numpy.random as nprandom

import ContextLogger
logger = ContextLogger.getLogger('')

config = None
random = None
CONDITIONAL_BEHAVIOUR = False

def load_config(config_file):
    '''Loads the passed config file into a python ConfigParser(). 
       
    :param config_file: (str) path to config
    '''
    global config
    config = ConfigParser.ConfigParser()
    if config_file is not None:
        try:
            config.read(config_file)
        except Exception as inst:
            print 'Failed to parse file', inst

    global CONDITIONAL_BEHAVIOUR 
    if config.has_option('DEFAULT','conditionalsimuser'):
        CONDITIONAL_BEHAVIOUR = config.getboolean('DEFAULT','conditionalsimuser')


def set_seed(seed):
    '''Intialise np random num generator

    :param seed: (int) 
    '''
    global random
    if seed is None:
        random = nprandom.RandomState()
    else:
        random = nprandom.RandomState(seed)


# END OF FILE
