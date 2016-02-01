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
HDCPolicy.py - Handcrafted dialogue manager
====================================================

Author: Dongho Kim  (Copyright CUED Dialogue Systems Group 2015)

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

import copy

import Policy
import DMUtils
import SummaryMapping
import Settings
import ContextLogger
logger = ContextLogger.getLogger(__name__)

MAX_NUM_ACCEPTED = 10


"""
Notes on proposed changes:
    this module only needs the list of system_requestable slots 
    - perhaps rather than passing a whole instance of DomainUtils.DomainUtils() - we could just pass the list ?

"""


class HDCPolicy(Policy.Policy):
    """Handcrafted policy overrides Policy base class.

        :param use_confreq: (bool). If true the policy is allowed to add a venue count in system actions, e.g. ``inform(count=20, food=chinese)``. This addition happens in summary-master mapping.
    """
    def __init__(self, use_confreq, domainUtil):
        """
        Handcrafted policy constructor.
        """
        super(HDCPolicy, self).__init__(use_confreq, domainUtil)
        # inherited from Policy.Policy() is self.domainUtil

    def work(self, belief):
        """Primary response function of HDC policy
        """
        global_summary = SummaryMapping.globalSummary(belief, domainUtil=self.domainUtil)
        array_slot_summary = SummaryMapping.arraySlotSummary(belief, self.domainUtil)
        logger.debug(str(global_summary))
        logger.debug('HDC policy: getGlobal')
        done, output = self._getGlobal(belief, global_summary)

        if not done:
            logger.debug('HDC policy: getConfirmSelect')
            done, output = self._getConfirmSelect(belief, array_slot_summary)
        if not done:
            logger.debug('HDC policy: getInform')
            inform_summary = []
            for num_accepted in range(1, MAX_NUM_ACCEPTED+1):
                temp = SummaryMapping.actionSpecificInformSummary(belief, num_accepted, self.domainUtil)
                inform_summary.append(temp)
                       
            done, output = self._getInform(belief, global_summary, inform_summary)
        if not done:
            logger.debug('HDC policy: getRequest')
            done, output = self._getRequest(belief, array_slot_summary)
        if not done:
            logger.warning("HDCPolicy couldn't find action: execute reqmore().")
            output = 'reqmore()'

        if output == 'badact()' or output == 'null()':
            logger.warning('HDCPolicy chose bad or null action')
            output = 'null()'

        if self.use_confreq:
            #TODO - known problem here if use_confreq is True (ie being used)  FIXME
            output = DMUtils.add_venue_count(output, belief)
        return output

    def _getGlobal(self, belief, global_summary):
        act = 'null()'

        if global_summary['GLOBAL_BYCONSTRAINTS'] > 0.5 and\
            global_summary['GLOBAL_COUNT80'] > 3:
            act = DMUtils.getGlobalAction(belief, 'INFORM_BYNAME', domainUtil=self.domainUtil)
        elif global_summary['GLOBAL_BYALTERNATIVES'] > 0.5:
            act = DMUtils.getGlobalAction(belief, 'INFORM_ALTERNATIVES', domainUtil=self.domainUtil)
        elif global_summary['GLOBAL_BYNAME'] > 0.5:
            act = DMUtils.getGlobalAction(belief, 'INFORM_REQUESTED', domainUtil=self.domainUtil )
        elif global_summary['GLOBAL_FINISHED'] > 0.5:
            act = DMUtils.getGlobalAction(belief, 'BYE', domainUtil=self.domainUtil)
        elif global_summary['GLOBAL_REPEAT'] > 0.5:
            act = DMUtils.getGlobalAction(belief, 'INFORM_REPEAT', domainUtil=self.domainUtil)
        elif global_summary['GLOBAL_REQMORE'] > 0.5:
            act = DMUtils.getGlobalAction(belief, 'INFORM_BYNAME', domainUtil=self.domainUtil)
        elif global_summary['GLOBAL_THANKYOU'] > 0.5:
            act = DMUtils.getGlobalAction(belief, 'REQMORE', domainUtil=self.domainUtil)
        elif global_summary['GLOBAL_ACK'] > 0.5:
            act = DMUtils.getGlobalAction(belief, 'REQMORE', domainUtil=self.domainUtil)
        elif global_summary['GLOBAL_RESTART'] > 0.5:
            act = DMUtils.getGlobalAction(belief, 'RESTART', domainUtil=self.domainUtil)

        if act != 'null()':
            return True, act
        return False, act

    def _getConfirmSelect(self, belief, array_slot_summary):
        for slot in self.domainUtil.sorted_system_requestable_slots:  
            # TODO - delete - Settings.ontology['system_requestable']:#Settings.ontology['informable']:
            summary = array_slot_summary[slot]
            (top_value, top_prob) = summary['TOPTWO'][0]
            (sec_value, sec_prob) = summary['TOPTWO'][1]
            if top_prob < 0.8:
                if top_prob > 0.6:
                    # Confirm
                    return True, 'confirm(%s="%s")' % (slot, top_value)
                elif top_prob > 0.3:
                    if top_prob - sec_prob < 0.2:
                        # Select
                        return True, 'select(%s="%s",%s="%s")' % (slot, top_value, slot, sec_value)
                    else:
                        # Confirm
                        return True, 'confirm(%s="%s")' % (slot, top_value)

        return False, 'null()'

    def _getInform(self, belief, global_summary, inform_summary):
        act = 'null()'

        count80 = global_summary['GLOBAL_COUNT80']
        offer_happened = global_summary['GLOBAL_OFFERHAPPENED']

        if count80 >= MAX_NUM_ACCEPTED:
            count80 = MAX_NUM_ACCEPTED - 1

        arr = inform_summary[count80]
        first = arr[0]  # True if there is no matching entities
        second = arr[1] # True if there is one matching entities
        #third = arr[2]  # True if there is two~four matching entities
        discr = arr[4]  # True if we can discriminate more

        logger.debug('%d among %d slots are accepted (>=0.8 belief).' % (count80, len(self.domainUtil.sorted_system_requestable_slots)))
        #logger.debug('%d among %d slots are accepted (>=0.8 belief).' % (count80, len(Settings.ontology['system_requestable'])))

        if first or second or not discr or count80 >= len(self.domainUtil.ontology['system_requestable']):  
            # If this inform gives either 0 or 1 or we've found everything we can ask about
            logger.debug('Trying to get inform action, have enough accepted slots.')
            logger.debug('Is there no matching entity? %s.' % str(first))
            logger.debug('Is there only one matching entity? %s.' % str(second))
            logger.debug('Can we discriminate more? %s.' % str(discr))
            requested_slots = DMUtils.getRequestedSlots(belief)

            if len(requested_slots) > 0 and offer_happened:
                logger.debug('Getting inform requested action.')
                act = DMUtils.getGlobalAction(belief, 'INFORM_REQUESTED', domainUtil=self.domainUtil)
            else:
                logger.debug('Getting inform exact action with %d accepted slots.' % count80)
                act = DMUtils.getInformAction(count80, belief, domainUtil=self.domainUtil)

        if act != 'null()':
            return True, act
        return False, act

    def _getRequest(self, belief, array_slot_summary):
        #slots = Settings.ontology['system_requestable']

        # This is added for confreq.
        need_grounding = DMUtils.getTopBeliefs(belief, 0.8, domainUtil=self.domainUtil)

        for slot in self.domainUtil.sorted_system_requestable_slots:  #slots:
            summary = array_slot_summary[slot]
            (_, topprob) = summary['TOPTWO'][0]
            (_, secprob) = summary['TOPTWO'][1]

            if topprob < 0.8:
                # Add implicit confirmation (for confreq.)
                grounding_slots = copy.deepcopy(need_grounding)
                if slot in grounding_slots:
                    del grounding_slots[slot]

                grounding_result = []
                for grounding_slot in grounding_slots:
                    if len(grounding_result) < 3:
                        (value, prob) = grounding_slots[grounding_slot]
                        grounding_result.append('%s="%s"' % (grounding_slot, value))

                if not grounding_result or not self.use_confreq:
                    return True, 'request(%s)' % slot
                else:
                    return True, 'confreq(' + ','.join(grounding_result) + ',%s)' % slot

        return False, 'null()'


#END OF FILE
