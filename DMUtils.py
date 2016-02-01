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
DMUtils.py - Dialogue manager utilities
====================================================

Authors: Dongho Kim, David Vandyke  (Copyright CUED Dialogue Systems Group 2015)

.. Note::
        DMUtils.py is a collection of utility functions only (No classes).

Local/file variables::
    
    ZERO_THRESHOLD:             unused
    REQUESTING_THRESHOLD:       affects getRequestedSlots() method

.. seealso:: CUED Imports/Dependencies: 

    import :class:`DiaAct` |.|
    from :class:`agentutils` |.|
    import :class:`ContextLogger`

************************

'''
__author__='donghokim, davidvandyke'
import copy

import agentutils
import DiaAct
import ContextLogger
logger = ContextLogger.getLogger('')

ZERO_THRESHOLD = 0.001
REQUESTING_THRESHOLD = 0.5


'''
Methods for belief states.
'''
def getRequestedSlots(belief):
    '''**Method for belief states:** Iterate over only goal slots

        :param belief: (dict) of dicts - full belief state 
        :returns: (list) of slot names with prob retrieved from belief > REQUESTING_THRESHOLD (an internal global)
    '''
    ans = []
    for slot in belief['beliefs']['requested']:
        requestprob = belief['beliefs']['requested'][slot]
        if requestprob > REQUESTING_THRESHOLD:
            ans.append(slot)
    return ans


def getTopBelief(slot_belief):
    '''**Method for belief states:** Return slot value with the largest belief

    :param slot_belief: (dict) of value:prob pairs for slot distribution
    :returns: top_value (str), top_belief (float)
    '''
    top_value = max(slot_belief.iterkeys(), key=(lambda key: slot_belief[key]))
    top_belief = slot_belief[top_value]
    return top_value, top_belief


def getTopBeliefs(belief, threshold='auto', domainUtil=None):
    '''**Method for belief states:** Get slot values with belief larger than threshold
    
    :param belief: (dict)
    :param threshold: (str or float) threshold on slot value probabilities. Default value is 'auto', only allowable string
    :param domainUtil: (instance) of :class:`DomainUtils`  
    :returns: (dict) as {slot: (topvalue, topbelief), ...}
    '''
    ans = {}
    for slot in domainUtil.ontology['system_requestable']:
        if threshold == 'auto':
            numvalues = len(domainUtil.ontology['informable'][slot])
            thres = 1. / (float(numvalues) - 0.1)
        else:
            thres = threshold

        topvalue, topbelief = getTopBelief(belief['beliefs'][slot])

        if topvalue != '**NONE**' and topbelief > thres:
            ans[slot] = (topvalue, topbelief)

    return ans


def getTopTwoBeliefsExcludingNone(slot_belief):
    '''**Method for belief states:** top two (value,belief) in slot 
    
    :param slot_belief: (dict) of value:prob pairs for slot distribution
    :returns: ans (list), is_top_none (bool) 
    '''
    slot_belief_copy = copy.deepcopy(slot_belief)
    ans = []
    is_top_none = False
    while len(ans) < 2 or len(slot_belief_copy) > 0:
        topvalue, topbelief = getTopBelief(slot_belief_copy)
        if len(ans) == 0 and topvalue == '**NONE**':
            is_top_none = True
        if topvalue != '**NONE**':
            ans.append((topvalue, topbelief))
        del slot_belief_copy[topvalue]

    return ans, is_top_none


'''
Methods for global action.
'''

def getGlobalAction(belief, globalact, domainUtil):
    '''**Method for global action:** returns action 

    :param belief: (dict) full belief state
    :param globalact: (int) - str of globalActionName, e.g. 'INFORM_REQUESTED'
    :param domainUtil: (instance) of :class:`DomainUtils.DomainUtils`
    :returns: (str) action
    '''

    # First get the name for the name goal.
    topvalue, topbelief = getTopBelief(belief['beliefs']['name'])
    toptwo, _ = getTopTwoBeliefsExcludingNone(belief['beliefs']['name'])
    if topvalue == '**NONE**' or topvalue == 'dontcare' or topbelief < 0.8:
        topnamevalue = ''
    else:
        topnamevalue = toptwo[0][0]

    lastInformedVenue = belief['features']['lastInformedVenue']
    informedVenueSinceNone = belief['features']['informedVenueSinceNone']
    acceptanceList = getTopBeliefs(belief, domainUtil=domainUtil)
    acceptanceList80 = getTopBeliefs(belief, 0.8, domainUtil=domainUtil)
    requestedSlots = getRequestedSlots(belief)

    # logger.debug('topnamevalue = %s, lastInformedVenue = %s' % (topnamevalue, lastInformedVenue))
    if topnamevalue == '' and lastInformedVenue != '':
        # logger.debug('topnamevalue is None, but copy lastInformedVenue')
        topnamevalue = lastInformedVenue

    if globalact == 'INFORM_REQUESTED':
        if topnamevalue != '':
            return _getInformRequestedSlots(acceptanceList80, requestedSlots, topnamevalue, domainUtil)
        else:
            return _getInformRequestedSlots(acceptanceList80, requestedSlots, 'none', domainUtil)
    elif globalact == 'INFORM_ALTERNATIVES':
        #if lastInformedVenue == '':
        #    print 'Cant inform alternatives no last informed venue'
        #    return 'null()'
        #else:
        return _getInformAlternativeEntities(acceptanceList, acceptanceList80, informedVenueSinceNone, domainUtil)
    elif globalact == 'INFORM_MORE':
        if len(informedVenueSinceNone) > 0 and topnamevalue != '':
            return _getInformMoreEntity(topnamevalue, domainUtil)
        else:
            return _getInformMoreEntity('none', domainUtil)
    elif globalact == 'INFORM_BYNAME':
        return _getInformAlternativeEntities(acceptanceList, acceptanceList80, [], domainUtil)
    elif globalact == 'INFORM_REPEAT':
        return 'null()'
    elif globalact == 'REQMORE':
        if lastInformedVenue != '':
            return 'reqmore()'
        else:
            return 'null()'
    elif globalact == 'BYE':
        return 'bye()'
    elif globalact == 'RESTART':
        return 'null()'
    else:
        logger.warning('Invalid global summary action name: '+globalact)
        return 'null()'


'''
Methods for global inform action.
'''
def computeInformAction(belief, numAccepted, domainUtil):
    '''**Method for global inform action:** returns summary inform action string 
    
    :param belief: (dict) full belief state
    :param numAccepted: (int) number of slots with prob. mass > 80
    :param domainUtil: (instance) of :class:`DomainUtils.DomainUtils` 
    :returns: summary action name, getInformAction(numAccepted,belief)
    '''
    summary_action_name = 'inform_' + str(numAccepted)
    return summary_action_name, getInformAction(numAccepted, belief, domainUtil=domainUtil)

def getInformAction(numAccepted, belief, domainUtil):
    '''**Method for global inform action:** returns inform act via getInformExactEntity() method \
            or null() if not enough accepted 
    
    :param belief: (dict) full belief state
    :param numAccepted: (int) number of slots with prob. mass > 80
    :param domainUtil: (instance) of :class:`DomainUtils.DomainUtils`
    :returns: getInformExactEntity(acceptanceList,numAccepted)
    '''

    acceptanceList = getTopBeliefs(belief, domainUtil=domainUtil)
    if numAccepted > len(acceptanceList):
        return 'null()'

    return getInformExactEntity(acceptanceList, numAccepted, domainUtil)


def getInformExactEntity(acceptanceList, numAccepted, domainUtil):
    '''**Method for global inform action:** creates inform act with none or an entity

    :param acceptanceList: (dict) of slots with value:prob mass pairs 
    :param numAccepted: (int) number of *accepted slots* (>80 prob mass)
    :param domainUtil: (instance) of :class:`DomainUtils.DomainUtils`
    :returns: getInformNoneVenue() or getInformAcceptedSlotsAboutEntity() as appropriate
    '''
    acceptedValues = {}
    for i, slot in enumerate(acceptanceList):
        if i >= numAccepted:
            break
        (topvalue, topbelief) = acceptanceList[slot]
        if topvalue != 'dontcare':
            acceptedValues[slot] = topvalue

    result = domainUtil.db.entity_by_features(acceptedValues)
    if len(result) == 0:
        return getInformNoneVenue(acceptedValues, domainUtil)
    else:
        ent = result[0]
        return getInformAcceptedSlotsAboutEntity(acceptanceList, ent, numAccepted)


def getInformNoneVenue(acceptedValues, domainUtil):
    '''**Method for global inform action:** creates inform(name=none,...) act

        :param acceptedValues: (dict) of accepted values
        :param domainUtil: (instance) of :class:`DomainUtils.DomainUtils`
        :returns: (str) inform(name=none,...) act
    '''
    feats = findMinimalAcceptedSetForNoEntities(acceptedValues, domainUtil)
    return 'inform(name=none, '+agentutils.convertFeatsToStr(feats)+')'


def findMinimalAcceptedSetForNoEntities(acceptedValues, domainUtil):
    '''**Method for global inform action:** drops accepted slots to allow a database entity to be found. 

        :param acceptedValues: (dict) of accepted values
        :param domainUtil: (instance) of :class:`DomainUtils.DomainUtils`
        :returns: (dict) acceptedvalues dict with at least one slot/constraint removed
    '''

    keeping = copy.deepcopy(acceptedValues)
    if len(acceptedValues) > 1:
        result = domainUtil.db.entity_by_features(acceptedValues)
        if len(result) == 0:
            for slot in acceptedValues:
                if slot != 'type':
                    del keeping[slot]  # removes current slot
                    result2 = domainUtil.db.entity_by_features(keeping)
                    if len(result2) > 0:
                        keeping[slot] = acceptedValues[slot] # adds it back if it (in combination) allows at least 1 entity 

    return keeping


def getInformAcceptedSlotsAboutEntity(acceptanceList, ent, numFeats):
    '''**Method for global inform action:** returns filled out inform() string
    need to be cleaned (Dongho)
    
    :param acceptanceList: (dict) of slots with value:prob mass pairs 
    :param ent: (dict) slot:value properties for this entity
    :param numFeats: (int) result of domainUtil.db.entity_by_features(acceptedValues)
    :returns: (str) filled out inform() act
    '''

    ans = 'inform('
    feats = {'name': ent['name']}

    for i, slot in enumerate(acceptanceList):
        if i >= numFeats:
            break
        if slot == 'name':
            continue

        (value, belief) = acceptanceList[slot]
        if value == 'dontcare' and slot in ent:
            feats[slot] = ent[slot]
        else:
            if slot in ent:
                feats[slot] = value
            else:
                logger.debug('Slot %s is not found in data for entity %s' % (slot, ent['name']))

    ans += agentutils.convertFeatsToStr(feats) + ')'
    return ans


def _getInformRequestedSlots(acceptanceList80, requestedSlots, name, domainUtil):
    result = domainUtil.db.entity_by_features({'name':name})

    acceptedValues = {}
    for slot in acceptanceList80:
        (topvalue, topbelief) = acceptanceList80[slot]
        if topvalue != 'dontcare':
            acceptedValues[slot] = topvalue

    if len(result) > 0 and name != 'none':
        # We found exactly one or more matching entities. Use the first one
        ent = result[0]
        return _getInformRequestedSlotsForEntity(acceptedValues, requestedSlots, ent)
    else:
        logger.debug('Couldn\'t find the provided name ' + name)
        # We have not informed about an entity yet, or there are too many entities.
        return 'null()'


def _getInformAlternativeEntities(acceptanceList, acceptanceList80, prohibitedList, domainUtil):
    '''
    Returns the dialogue act representing either
    1) there is not matching venue: inform(name=none, slot=value, ...)
    2) it offers a venue which is not on the prohibited list
    3) if all matching venues are on the prohibited list then it says
       there is no venue except x,y,z,... with such features:
       inform(name=none, name!=x, name!=y, name!=z, ..., slot=value, ...)
    '''
    acceptedValues = {}
    numFeats = len(acceptanceList80)
    for slot in acceptanceList80:
        (topvalue, topbelief) = acceptanceList80[slot]
        if topvalue != 'dontcare':
            acceptedValues[slot] = topvalue

    if len(acceptedValues) == 0:
        logger.warning("User didn't specify any constraints or all are dontcare")
        #return 'null()'

    result = domainUtil.db.entity_by_features(acceptedValues)
    if len(result) == 0:
        return getInformNoneVenue(acceptedValues, domainUtil)
    else:
        for ent in result:
            name = ent['name']
            if name not in prohibitedList:
                return getInformAcceptedSlotsAboutEntity(acceptanceList, ent, numFeats)

        return getInformNoMoreVenues(acceptanceList, result, numFeats)

    return 'null()'


def getInformNoMoreVenues(acceptanceList, entities, numFeats):
    '''**Method for global inform action:** returns inform(name=none, other than x and y, with constraints w and z) act   

        :param acceptanceList: (dict) of slots with value:prob mass pairs 
        :param entities: (list) of database entity dicts
        :param numFeats: (int) number of constraints
        :returns: (str) inform() action
    '''

    ans = 'inform(name=none,'

    for ent in entities:
        ans += 'name!="' + ent['name'] + '",'

    feats = {}
    for count, slot in enumerate(acceptanceList):
        if count >= numFeats:
            break

        if slot == 'name':
            continue

        (value, belief) = acceptanceList[slot]
        if value == 'dontcare':
            continue

        feats[slot] = value

    ans += agentutils.convertFeatsToStr(feats) + ')'
    return ans


def _getInformMoreEntity(name, domainUtil):
    '''
    Finds the last informed entity and it informs about the non-accepted slots.
    @param name the last informed entity
    '''
    result = domainUtil.db.entity_by_features({'name':name})
    if name != 'none' and len(result) > 0:
        ent = result[0]
        return _getInformCommentSlotAboutEntity(ent)
    else:
        return 'null()'

def _getInformCommentSlotAboutEntity(ent):

    output = 'inform(name="%s"' % ent['name']
    if 'comment' in ent:
        output += ',comment="%s"' % ent['comment']
    if 'type' in ent:
        output += ',type="%s"' % ent['type']
    output += ')'
    return output

def _getInformRequestedSlotsForEntity(acceptedValues, requestedSlots, ent):
    '''
    @param acceptedValues sufficiently confident slot values
    @param requestedSlots list of requested slots
    should be improved: acceptedValues may not be needed
    '''
    #print 'requested slots: ', requestedSlots

    ans = 'inform('

    slotvaluepair = ['name="'+ent['name']+'"']
    if len(requestedSlots) == 0:
        slotvaluepair += ['type="'+ent['type']+'"']

    # Should inform about requested slots.
    for i in range(len(requestedSlots)):
        slot = requestedSlots[i]

        if i > 5:
            break

        if slot == 'name' or slot == 'location':
            break

        acceptedValue = ''
        requestedSlotFound = False

        if slot in acceptedValues:
            acceptedValue = acceptedValues[slot]

        if slot in ent:
            slotvaluepair.append(slot+'="'+ent[slot]+'"')
#            if slot in ent and acceptedValue == ent[slot]:
#                slotvaluepair.append(slot+'="'+acceptedValue+'"')
#            elif slot in ent and not slot in acceptedValues:
#                '''
#                added only if its value is not accepted
#                '''
#                slotvaluepair.append(slot+'="'+ent[slot]+'"')
        else:
            slotvaluepair.append(slot+'=none')

    ans += ','.join(slotvaluepair) + ')'
    return ans


'''
Slot-level actions.
'''
def getSlotLevelAction(belief, slot, action, disableLowProbAct=False, domainUtil=None):
    '''**Slot-level actions:** forms slot level action 
    
        :param belief: (dict) full belief state
        :param slot: (str) 
        :param actions: (int) 0-request, 1-confirm, 2-select
        :param disableLowProbAct: (bool  [Default=False])  
        :param domainUtil: (instance) of :class:`DomainUtils.DomainUtils` [Default=None]
        :returns: summary action name (str), master slot action (str)
    '''
    # number of possible slot values excluding N/A
    numvalues = len(domainUtil.ontology["informable"][slot])
    minBeliefForConfirm = 1.0 / (float(numvalues)-0.1)

    # Get top two beliefs
    toptwo, _ = getTopTwoBeliefsExcludingNone(belief['beliefs'][slot])
    topvalue = toptwo[0][0]
    topbelief = toptwo[0][1]

    if action == 0: # Request.
        summaryActionName = "request_" + slot
        output = "request("

        # Add implicit confirmation
        needGrounding = getTopBeliefs(belief, 0.8, domainUtil=domainUtil)
        if slot in needGrounding:
            del needGrounding[slot]
        acceptanceList = getTopBeliefs(belief, domainUtil=domainUtil)

        if len(acceptanceList) > 0 and len(needGrounding) > 0:
            foundThis = False
            if slot in acceptanceList:
                (_, prob) = acceptanceList[slot]
                if prob > 0.8:
                    foundThis = True

            # If there is no accepted value, add implicit confirmation
            if not foundThis:
                output = "confreq("
                slotvaluepair = []
                for slotname in needGrounding:
                    if len(slotvaluepair) < 3:
                        (value, prob) = needGrounding[slotname]
                        slotvaluepair.append(slotname + '="' + value + '"')
                output = output + ','.join(slotvaluepair) + ','

        output = output + slot + ')'

    elif action == 1: # Confirm.
        summaryActionName = "confirm_" + slot
        if not disableLowProbAct or topbelief > minBeliefForConfirm:
            output = 'confirm(%s="%s")' % (slot, topvalue)
        else:
            output = 'null()'

    elif action == 2: # Select.
        summaryActionName = "select_" + slot
        if not disableLowProbAct or (topbelief > minBeliefForConfirm and len(toptwo) == 2):
            output = 'select(%s="%s",%s="%s")' % (slot, topvalue, slot, toptwo[1][0])
        else:
            output = 'null()'

    else:
        summaryActionName = "invalid_" + slot
        output = 'null()'

    return summaryActionName, output


def add_venue_count(input, belief, domainUtil):
    '''Add venue count.

    :param input: String input act.
    :param belief: Belief state
    :param domainUtil: (instance) of :class:`DomainUtils.DomainUtils`
    :returns: act with venue count.
    '''
    acceptanceList = getTopBeliefs(belief, domainUtil=domainUtil)
    accepted_slots = {}
    for i, slot in enumerate(acceptanceList):
        (topvalue, topbelief) = acceptanceList[slot]
        if topvalue != 'dontcare':
            accepted_slots[slot] = topvalue

    count = len(domainUtil.db.entity_by_features(accepted_slots))
    input_act = DiaAct.DiaAct(input)
    if input_act.act == 'confreq':
        if count > 1:
            output = copy.deepcopy(input_act)
            for slot in accepted_slots:
                val = accepted_slots[slot]
                if not input_act.contains(slot, val):
                    output.append_front(slot, val)

            output.append_front('count', str(count))
            return str(output)
    #     else:
    #         logger.warning('accepted slots: ' + str(accepted_slots))
    #         logger.error('badact in add_venue_count: input=%s, count=%d' % (input, count))
    #         return 'badact()'
    # elif count <=1 and len(accepted_slots) > 0 and input_act.act in ['confirm', 'request', 'select']:
    #     logger.warning('accepted slots: ' + str(accepted_slots))
    #     logger.error('badact in add_venue_count: input=%s, count=%d' % (input, count))
    #     return 'badact()'
    return input

#END OF FILE
