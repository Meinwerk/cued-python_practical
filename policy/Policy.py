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
Policy.py - 
====================================================

Author: Dongho Kim  (Copyright CUED Dialogue Systems Group 2015)

.. seealso:: CUED Imports/Dependencies: 

    import :class:`Settings
    import :class:`DMUtils`
    import :class:`ContextLogger`

.. warning::
        Documentation not done.


************************

'''

"""
Notes on proposed changes:
    Need: remove Settings.ontology dependence
    this module only needs the list of system_requestable slots 
    - perhaps rather than passing a whole instance of DomainUtils.DomainUtils() - we could just pass the list ?

"""


import Settings
import DMUtils
import ContextLogger
import DomainUtils
from policy import SummaryAction
logger = ContextLogger.getLogger('')


class Policy(object):
    def __init__(self, use_confreq, domainUtil):
        """
        Sets the number of possible system actions (self.numActions and self.numSlotActions).
        See SlotBasedActionList in the vocaliq system
        :param use_confreq: boolean. If true the policy is allowed to add a venue count in system actions,
        e.g. inform(count=20, food=chinese). This addition happens in summary-master mapping.
        """
        self.use_confreq = use_confreq
        #self.sorted_slots = Settings.ontology['system_requestable']
        self.domainUtil = domainUtil

        self.disableLowProbAct = False  #TODO - can make this a config variable if actually used

        # action information are all maintained in a class SummaryAction.SummaryAction
        self.actions = SummaryAction.SummaryAction(domainUtil)
        # Total number of system actions.
        self.numActions = len(self.actions.action_names)

        logger.debug("numActions = "+str(self.numActions))

        # Trajectory for policy training
        self.last_belief = None
        self.last_act = None
        self.last_rew = None
        self.belief = None
        self.act = None
        
    def work(self, belief):
        '''
        This base Policy class performs pre- and post-processing of system action selection.
        1. Preprocessing: It converts all summary actions to master actions and checks whether they are executable.
        2. Action selection: This is done in overridden "select" method of a child class,
                             which returns an index of selected action.
        3. Postprocessing: Converts selected action index to master action and adds count=.
        If the policy doesn't need these pre- and post-processing, It can override this work method.
        :return: system action in string
        '''
        # 1. Preprocessing: Get executable actions.
        executable = []
        all_action_list = []
        for a in range(self.numActions):
            summary, sys_act = self.to_master_action(a, belief, self.last_act)
            all_action_list.append(sys_act)
            if not sys_act.startswith('null'):
                executable.append(a)

        # 2. Action selection.
        self.last_belief = self.belief
        self.last_act = self.act
        act_index = self.select(belief, executable)
        self.belief = belief
        self.act = act_index

        # 3. Postprocessing.
        output = all_action_list[act_index]
        if self.use_confreq:
            output = DMUtils.add_venue_count(output, belief, self.domainUtil)
        return output

    def select(self, belief, executable):
        pass

    def train(self, rew):
        '''
        This method is called by DMan, after observing reward, updating belief and getting the optimal action
        in "work" method. For example,
        (self.belief, self.act, rew) for Q-learning.
        (self.last_belief, self.last_act, self.last_rew, self.belief, self.act) for SARSA.
        '''
        self.last_rew = rew

    def end_episode(self):
        pass

    def to_master_action(self, actionIdx, belief, lastActionIdx):
        '''
        Maps the given action index to summary action name and action.
        '''
        actionName = self.actions[actionIdx]
        lastActionName = self.actions[lastActionIdx]
        return self.actions.Convert(belief, actionName, lastActionName)
        logger.error('The given action number is invalid: %d' % action)

    def save(self, filename):
        pass

    def load(self, filename):
        '''
        Initialises with the given policy file. If the file doesn't exist, parameters might be randomly initialised
        depending on the policy type.
        :param filename:
        :return:
        '''
        pass


#END OF FILE
