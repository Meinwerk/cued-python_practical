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
MCCPolicy.py - Monte Carlo Control algorithm on grid-based dialogue state
============================================

Author: Pei-Hao (Eddy) Su  (Copyright CUED Dialogue Systems Group 2015)

   
**Relevant Config variables** [Default values]::

    [mccpolicy]
    gamma = 1.0
    nu = 0.0001
    epsilon_start = 1.0
    epsilon_end = 0.1
    maxIter = 2000

.. seealso:: CUED Imports/Dependencies: 

    import :class:`Policy` |.|
    import :class:`DMUtils` |.|
    import :class:`SummaryMapping` |.|
    import :class:`Settings` |.|
    import :class:`ContextLogger`
 
.. warning::
        Documentation not done.

************************

'''


__author__ = 'phs26'

import json
import pickle
import os
import sys
import cStringIO, tokenize
#import cPickle as pickle

# Belief tracker
from collections import defaultdict

import numpy as np
import random
import math
import copy
from collections import deque
from collections import OrderedDict
from scipy import linalg, mat, dot

import GPPolicy
import DMUtils
import DomainUtils
import Policy
import SummaryAction
import Settings
import ContextLogger
logger = ContextLogger.getLogger(__name__)

import itertools

class DataPoint(object):
    def __init__(self, b, a):
        self.b = b  # belief point
        self.a = a  # action

    def __eq__(self, other):
        return (self.b  == other.b  and
                self.a  == other.a)

class DataPointValue(object):
    def __init__(self, Q, N):
        self.Q = Q  # Q value
        self.N = N  # N count

    def __eq__(self, other):
        return (self.Q  == other.Q  and
                self.N  == other.N)

class MCCPolicy(Policy.Policy):
    def __init__(self, in_policyFile, out_policyFile, use_confreq=True, is_training=False, domainUtil=None):
        super(MCCPolicy, self).__init__(use_confreq, domainUtil)
       
        self.in_policyFile = in_policyFile
        self.out_policyFile = out_policyFile
        self.is_training = is_training
        self.domainUtil = domainUtil

        # by phs26, calling summary actions from SummaryAction.py
        self.actions = SummaryAction.SummaryAction(domainUtil)
        self.numActions = len(self.actions.action_names)

        logger.info('is it training? : ' + str(self.is_training))

        '''
        Initialise MCC policy structure.
        '''
        self.gamma = 1.0
        if Settings.config.has_option('mccpolicy_'+domainUtil.domainString, 'gamma'):
            self.gamma = Settings.config.getfloat('mccpolicy_'+domainUtil.domainString, 'gamma')
       
        self.nu = 0.0001
        if Settings.config.has_option('mccpolicy_'+domainUtil.domainString, 'nu'):
            self.nu = Settings.config.getfloat('mccpolicy_'+domainUtil.domainString, 'nu')
        
        self.epsilon_start = 1.0
        if Settings.config.has_option('mccpolicy_'+domainUtil.domainString, 'epsilon_start'):
            self.epsilon_start = Settings.config.getfloat('mccpolicy_'+domainUtil.domainString, 'epsilon_start')
        
        self.epsilon_end = 0.1
        if Settings.config.has_option('mccpolicy_'+domainUtil.domainString, 'epsilon_end'):
            self.epsilon_end = Settings.config.getfloat('mccpolicy_'+domainUtil.domainString, 'epsilon_end')
        
        self.maxIter = 2000
        if Settings.config.has_option('mccpolicy_'+domainUtil.domainString, 'maxIter'):
            self.maxIter = Settings.config.getfloat('mccpolicy_'+domainUtil.domainString, 'maxIter')

        self.epsilon = 1
        
        self.max_k = 5
        if Settings.config.has_option('mccpoilcy_'+domainUtil.domainString, 'max_k'):
            self.max_k = Settings.config.getint('mccpoilcy_'+domainUtil.domainString, 'max_k')

        self.policyfeatures = []
        if Settings.config.has_option('mccpolicy_'+domainUtil.domainString, 'features'):
            logger.info('Features: ' + str(Settings.config.get('mccpolicy_'+domainUtil.domainString, 'features')))
            self.policyfeatures = json.loads(Settings.config.get('mccpolicy_'+domainUtil.domainString, 'features'))

        self.ready()

    def ready(self):
        '''
        Initialise MCC private members.
        '''
        self.statePath = []
        self.actionPath = []
        self.rewardPath = []

        self.dictionary = {}
        self.uncertainty = []
        self.policy = []

        if self.is_training:
            # Training data
            self.data_b = None
            self.data_a = None
            self.data_r = None

        self.totalepisodeCnt = 0
       
        self.load(self.in_policyFile)
        print 'loaded episode number: ', self.totalepisodeCnt

    #def learningStep(self, belief, action, reward):

    def distanceState(self, belief1, belief2):
        '''
        Calculate distance between two beliefs by 1 - (cosine similarity)
        '''
        if len(belief1) != len(belief2):
            return 2.0
        b1 = mat(belief1)
        b2 = mat(belief2)
        cosSim = dot(b1,b2.T)/linalg.norm(b1)/linalg.norm(b2)
        return 1.0 - cosSim[0,0]
    
    def distanceAction(self, action1, action2):
        '''
        Calculage distance between two actions by delta function
        '''
        if action1 == action2:
            return 0.0
        else:
            return 1.0

    def findClosest(self, belief, action):
        '''
        Find the closest grid point in the dictionary to the current (belief, action) pair
        '''
        closestDP = None
        closestValue = float('Inf')
        for dp in self.dictionary.keys():
            if self.distanceAction(dp.a, action) == 0.0 \
                and self.distanceState(dp.b, belief) < closestValue:
                    
                closestValue = self.distanceState(dp.b, belief)
                closestDP = dp
        
        return closestDP, closestValue

    def ShowDictionary(self):
        '''
        Show dictionary grid points and their corresponding Q values
        '''

        print 'dictionary points:', len(self.dictionary)
        for key, value in self.dictionary.items():
            print key.b, key.a, value.Q, value.N


    def UpdatePolicy(self):
        '''
        Scan the episode and update the cumulative total return to each (b,a) pair
        '''

        if (self.data_b, self.data_a ,self.data_r) == (None, None, None): 
            return

        Return = 0.0
        for b, a, r in zip(self.data_b[::-1], self.data_a[::-1], self.data_r[::-1]):
            closestDP, closestValue = self.findClosest(b,a)
            Return = self.gamma * Return + r

            #####################################################################
            # TODO:                                                             #
            # Complete the following policy update part in three different      #
            # scenarios: 1. size(self.dictionary) = 0                           #
            #            2. closest grid point in self.dictionary > self.nu     #
            #            3. closest grid point in self.dictionary <= self.nu    #
            # Follow the description of the MCC alg. in the practical note.     #
            #####################################################################

            # HINT: use class DataPoint and DataPointValue and self.dictionary

            if len(self.dictionary) == 0.0:
                logger.debug('starting a new dictionary')
                
                # your code here...
                # add (b,a) with Q=Return and N=1.0
                self.dictionary[DataPoint(b,a)]= DataPointValue(r, 1.0)

            elif closestDP is None or closestValue > self.nu:
                logger.debug('adding new point')
                
                # your code here...
                # add (b,a) with Q=Return and N=1.0
                self.dictionary[DataPoint(b,a)]= DataPointValue(r, 1.0)
            else:
                logger.debug('updating Q & N of the grid point')
                # your code here...
                # update Q and N with monte carlo algorithm
                currValue = self.dictionary[DataPoint(b,a)]
                newN = currValue.N + 1.0
                newQ = 1.0*(currValue.Q*currValue.N + r) / newN
                self.dictionary[DataPoint(b,a)]= DataPointValue(newQ, newN)

        # reset episodic data to None
        self.data_b = None 
        self.data_a = None
        self.data_r = None

    def savePolicy(self):
        pass
        #self.savePolicyInc(self.out_policyFile)

    def savePolicyInc(self, filename):
        '''
        Save the dictionary to a pickle file
        '''
        logger.info("Saving to %s ..." % filename)
        f = open(filename, 'wb')
        for obj in [self.dictionary]: # save data points with value, Q and N
            pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)
        f.close()

        #self.ShowDictionary()
        print 'number of dictionary points:', len(self.dictionary)

    def load(self, filename):
        '''
        Load the dictionary from a pickle file
        '''
        if os.path.isfile(filename):
            logger.info('Successfully loading policy %s.' % filename)
            f = open(filename, 'rb')

            loaded_objects = []
            for i in range(1): # load nn params and collected data
                loaded_objects.append(pickle.load(f))

            self.dictionary = copy.deepcopy(loaded_objects[0])
         
            f.close()
        else:
            #logger.error('Policy not found: %s.' % filename)
            logger.info('Policy not found: %s.' % filename)
        
        if self.is_training:
            logger.info('Start learning policy: %s.' % filename)

    def select(self, belief, action_names, actionObj, lastAction):
        '''
        epsilon-greedy policy
        :return: system action (string) and action index.
        '''
        # Get admissible actions
        admissible = []
        not_admissible = []
        admissMask = []
        all_action_list = []
        for a in range(self.numActions):
            #summary, sys_act = self.to_master_action(a, belief)
            sys_act = actionObj.Convert(belief, actionObj.action_names[a], lastAction)
            all_action_list.append(sys_act)
            if not sys_act.startswith('null'):
                admissible.append(a)
                admissMask.append(1.0)
            else:
                not_admissible.append(a)
                admissMask.append(0.0)
        
        for i in range(len(all_action_list)):
            if not 'null' in all_action_list[i]:
                logger.debug('actions: %s, %i' % (all_action_list[i], admissMask[i]))

        # Action selection.
        if self.is_training and Settings.random.rand() < self.epsilon:
            # Random action.
            action = Settings.random.choice(admissible)
        else:


            gpstate = GPPolicy.GPState(belief, replace={}, domainUtil=self.domainUtil)
            flat_belief = self.flatten_belief(gpstate)

            #####################################################################
            # TODO:                                                             #
            # Complete the following episode generation with epsilon greedy.    #
            # Implement the greedy action part.                                 # 
            # Follow the description of the MCC alg. in the practical note.     #
            #####################################################################

            # HINT: 1. admissible list are executable action given a belief
            #       2. use the function self.findClosest(b,a)
            #       3. use flat_belief (type: list) instead of belief (type: dict), and pass it to function 'findClosest'

            # your code here...
            # choose the action index with the highest corresponding Q given a belief b
            action = max(admissible, key=lambda a: self.findClosest(flat_belief, a)[1].Q)

        return action_names[action], action


    def flatten_belief(self, gpstate):
        '''
        Flatten the GP-dictionary-typed belief state to a one-dim vector
        '''
        flat_belief = []
        for key, value in gpstate._bstate.items():
            for i in value:
                flat_belief += i

        return flat_belief
    
    '''
    Methods for training policy.
    '''

    def train(self, r):
        super(MCCPolicy, self).train(r)


    def recordExecutedAction(self, b, a, r):
        '''
        Collect and Save training data.
        '''
        if not self.is_training:
            return

        gpstate = GPPolicy.GPState(b, replace={}, domainUtil=self.domainUtil)
        b = self.flatten_belief(gpstate)
       
        belief = [b]
        action = [a]
        reward = [r]

        # Initialise data varaibles
        if self.data_b is None:
            self.data_b = belief
            self.data_a = action
            self.data_r = reward
        else:

            self.data_b = self.data_b + belief
            self.data_a = self.data_a + action
            self.data_r = self.data_r + reward
        
        super(MCCPolicy, self).train(r)


    def startLearningEpisode(self, episodeNum):
        '''
        Set epislon parameter 
        '''
        logger.info('start training episode')
        
        # anneal and update epsilon
        self.epsilon = self.epsilon_start - (self.epsilon_start - self.epsilon_end) * float(episodeNum) / float(self.maxIter)

    def endLearningEpisode(self):
        '''
        Update and save the policy
        '''

        if self.is_training:
            logger.info('it is training!')
        else:
            logger.info("not training, return.")
            return

        logger.info("Updating MCC policy parameters.")
        
        self.UpdatePolicy()
        self.totalepisodeCnt += 1
        
        logger.info('total length of episode so far:', self.totalepisodeCnt)
           
        if self.totalepisodeCnt % 10 == 0:
            self.savePolicyInc(self.out_policyFile)

        print 'dictionary points:', len(self.dictionary)
