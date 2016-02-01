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
SelectPolicy.py - defers control to human expert  
==================================================

Author: Dongho Kim  (Copyright CUED Dialogue Systems Group 2015)

.. seealso:: CUED Imports/Dependencies: 

    import :class:`Policy`
    import :class:`ContextLogger`

.. warning::
        Documentation not done.


************************

'''


import Policy
import ContextLogger
logger = ContextLogger.getLogger(__name__)


class SelectPolicy(Policy.Policy):
    '''Derived from :class:`Policy`
    '''
    def __init__(self, use_confreq=True):
        super(SelectPolicy, self).__init__(use_confreq)

    def select(self, belief, executable):
        '''
        policy from experts

        :param belief: 
        :param executable:
        :returns: (int) representing action
        '''
        all_action_list = []
        for a in range(self.numActions):
            summary, sys_act = self.to_master_action(a, belief, self.last_act)
            all_action_list.append(sys_act)
            print a, summary, sys_act

        action = int(raw_input('sys> '))
        return action

#END OF FILE
