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
