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
SummaryMapping.py - summarises dialog events 
==============================================

Authors: Dongho Kim, David Vandyke  (Copyright CUED Dialogue Systems Group 2015)

**Basic Usage**: 
    >>> import SummaryMapping   
   
.. Note::

        No classes; collection of utility methods

Local/file variables::

    global_summary_features:    (list) global actions/methods
    ZERO_THRESHOLD:             (float) 0.001 min prob value to be considered non-zero

.. seealso:: CUED Imports/Dependencies: 

    import :class:`DMUtils` |.|
    import :class:`Settings`

************************

'''
__author__ = "donghokim, davidvandyke"

import numpy as np

import DMUtils
import Settings

global_summary_features = ['GLOBAL_BYCONSTRAINTS',
                           'GLOBAL_BYALTERNATIVES',
                           'GLOBAL_BYNAME',
                           'GLOBAL_FINISHED',
                           'GLOBAL_REPEAT',
                           'GLOBAL_REQMORE',
                           'GLOBAL_THANKYOU',
                           'GLOBAL_ACK',
                           'GLOBAL_RESTART',
                           'GLOBAL_COUNT80',
                           'GLOBAL_NAMENONE',
                           'GLOBAL_OFFERHAPPENED']
                           #'GLOBAL_REQUESTED_SLOTS']

ZERO_THRESHOLD = 0.001


def globalSummary(belief, domainUtil):
    '''summary of global actions such as offer happened etc.

        :param belief: (dict) full belief state
        :returns: (dict) summary. dict keys are given by :meth:`global_summary_features` 
    '''
    topMethod, topMethodBelief = DMUtils.getTopBelief(belief['beliefs']['method'])
    topDiscourseAct, topDiscourseActBelief = DMUtils.getTopBelief(belief['beliefs']['discourseAct'])
    if topMethod == 'byconstraints':
        globalpoint = 'GLOBAL_BYCONSTRAINTS'
    elif topMethod == 'byalternatives':
        globalpoint = 'GLOBAL_BYALTERNATIVES'
    elif topMethod == 'byname':
        globalpoint = 'GLOBAL_BYNAME'
    elif topMethod == 'finished' and topMethodBelief > 0.5:
        globalpoint = 'GLOBAL_FINISHED'
    elif topMethod == 'restart' and topMethodBelief > 0.5:
        globalpoint = 'GLOBAL_RESTART'
    else:
        globalpoint = 'GLOBAL_BYCONSTRAINTS'

    if topDiscourseAct == 'repeat' and topDiscourseActBelief > 0.5:
        globalpoint = 'GLOBAL_REPEAT'
    elif topDiscourseAct == 'reqmore' and topDiscourseActBelief > 0.5:
        globalpoint = 'GLOBAL_REQMORE'
    elif topDiscourseAct == 'thankyou' and topDiscourseActBelief > 0.5:
        globalpoint = 'GLOBAL_THANKYOU'
    elif topDiscourseAct == 'ack' and topDiscourseActBelief > 0.5:
        globalpoint = 'GLOBAL_ACK'

    summaryArray = dict.fromkeys(global_summary_features, False)
    summaryArray[globalpoint] = True
    summaryArray['GLOBAL_COUNT80'] = len(DMUtils.getTopBeliefs(belief, domainUtil=domainUtil))
    summaryArray['GLOBAL_NAMENONE'] = belief['features']['lastActionInformNone']
    summaryArray['GLOBAL_OFFERHAPPENED'] = belief['features']['offerHappened']

    return summaryArray


def arraySlotSummary(belief, domainUtil): 
    '''Gets the summary vector for goal slots, including the top probabilities, entropy, etc.

    :param belief: (dict) full belief state
    :return: (dict) of slot goal summaries
    '''
    summary = {}
    for slot in domainUtil.sorted_system_requestable_slots:
        #Settings.ontology['system_requestable']:#Settings.ontology['informable']:
        summary[slot] = {}
        slot_belief = belief['beliefs'][slot]
        summary[slot]['TOPTWO'], summary[slot]['ISTOPNONE'] = \
            DMUtils.getTopTwoBeliefsExcludingNone(belief['beliefs'][slot])
        belief_dist = slot_belief.values()
        filtered_dist = filter(lambda prob: prob > ZERO_THRESHOLD, belief_dist)
        summary[slot]['ENTROPY'] = filtered_dist * np.log(filtered_dist)

        # Array indicating whether 'request' has top probability
        summary[slot]['ISREQUESTTOP'] = belief['beliefs']['requested'][slot] > 0.5
    return summary


def actionSpecificInformSummary(belief, numAccepted, domainUtil):
    '''count: # of entities matching with numAccepted slots in acceptance list.

        :param belief: (dict) full belief state
        :param numAccepted: (int) 
        :param informable_slots: (list)
        :returns: summary_array [count==0, count==1, 2<=count<=4, count>4, discriminatable] \  discriminatable: matching entities can be further discriminated
    '''
    acceptanceList = DMUtils.getTopBeliefs(belief, domainUtil=domainUtil)
    count = _countEntitiesForAcceptanceListPart(acceptanceList, numAccepted, domainUtil)
    discriminatable = _acceptanceListCanBeDiscriminated(acceptanceList, numAccepted, domainUtil)
    summary_array = [count == 0, count == 1, 2 <= count <= 4, count > 4, discriminatable]
    return summary_array


def _countEntitiesForAcceptanceListPart(acceptanceList, numAccepted, domainUtil):
    '''
    Returns the number of entities matching the first self.maxAcceptedSlots (default=10)
    values in the acceptance list. Includes values with dontcare in the count

    :param acceptanceList: {slot: (topvalue, topbelief), ...}
    :param numAccepted: (int)
    :returns: (int) number of entities
    '''
    acceptedValues = {}
    countVals = 0
    countEnts = 40

    for slot in acceptanceList:
        (topvalue, _) = acceptanceList[slot]
        if topvalue != 'dontcare':
            acceptedValues[slot] = topvalue
        countVals += 1
        if countVals >= numAccepted:
            break

    if len(acceptedValues) > 0:
        result = domainUtil.db.entity_by_features(acceptedValues)  #Settings.db.entity_by_features(acceptedValues)
        countEnts = len(result)

    return countEnts


def _acceptanceListCanBeDiscriminated(acceptanceList, numAccepted, domainUtil):
    '''
    Checks if the given acceptance list with the given number of values accepted
    returns a list of values which can be discriminated between -
    i.e. there is a question which we could ask which would give differences between
    the values.
    Note that only slots from the full acceptanceList (i.e. not just below
    maxAcceptedSlots are used for discrimination to exclude things like phone, addr, etc)

    :param acceptanceList:
    :param numAccepted: (int)
    :returns: (bool) answering discrimination question
    '''
    acceptedValues = {}
    discriminatingSlots = set()
    i=0
    for slot in acceptanceList:
        if i < numAccepted:
            (topvalue, _) = acceptanceList[slot]
            if topvalue != 'dontcare':
                acceptedValues[slot] = topvalue
        else:
            discriminatingSlots.add(slot)
        i += 1

    for slot in domainUtil.informable_slots: 
        if slot != 'name':
            discriminatingSlots.add(slot)

    result = domainUtil.db.entity_by_features(acceptedValues)#Settings.db.entity_by_features(acceptedValues)

    otherFeats = {}
    for ent in result:
        for slot in ent:
            val = ent[slot]

            # this slot was one of the constraints or dontcare
            if slot not in acceptedValues and slot in discriminatingSlots:
                if slot not in otherFeats or otherFeats[slot] == val:
                    otherFeats[slot] = val
                else:
                    # This slot will allow discrimination and isn't in the constraints
                    return True

    return False

#END OF FILE
