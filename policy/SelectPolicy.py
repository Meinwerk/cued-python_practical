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
