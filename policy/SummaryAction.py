'''
SummaryAction.py - 
============================================

Author: Milica Gasic  (Copyright CUED Dialogue Systems Group 2015)

.. seealso:: CUED Imports/Dependencies: 

    import :class:`SummaryMapping` |.|
    import :class:`Settings` |.|
    import :class:`DMUtils` |.|
    import :class:`ContextLogger`

.. warning::
        Documentation not done.

************************

'''

__author__ = 'milicagasic'

import SummaryMapping
import Settings
import DMUtils
import ContextLogger
logger = ContextLogger.getLogger('')

MAX_NUM_ACCEPTED = 10

class SummaryAction():
    '''
    :param domainUtil: (instance) of :class:`DomainUtils.DomainUtils`
    '''
    def __init__(self, domainUtil):
        self.domainUtil = domainUtil 
        self.action_names = []
        for slot in self.domainUtil.ontology['system_requestable']:
            self.action_names.append("request_"+slot)
            self.action_names.append("confirm_"+slot)
            self.action_names.append("select_"+slot)
        self.action_names += [  "inform", 
                                "inform_byname", 
                                "inform_alternatives", 
                                "inform_requested", 
                                "bye", 
                                "repeat", 
                                "reqmore", 
                                "restart"
                            ]


    def getRequest(self, belief, slot):
        '''
        '''
        array_slot_summary = SummaryMapping.arraySlotSummary(belief, self.domainUtil)
        summary = array_slot_summary[slot]
        (_, topprob) = summary['TOPTWO'][0]
        (_, secprob) = summary['TOPTWO'][1]

        #if topprob < 0.4 and secprob<= 0.3:
        return True, 'request(%s)' % slot
        #return False, 'null()'

    def getConfirm(self, belief,slot):
        '''
        '''
        array_slot_summary = SummaryMapping.arraySlotSummary(belief, self.domainUtil)
        summary = array_slot_summary[slot]
        (top_value, top_prob) = summary['TOPTWO'][0]
        (sec_value, sec_prob) = summary['TOPTWO'][1]
        if top_prob > 0:
            return True, 'confirm(%s="%s")' % (slot, top_value)
        return False, 'null()'

    def getSelect(self,belief, slot):
        '''
        '''
        array_slot_summary = SummaryMapping.arraySlotSummary(belief, self.domainUtil)
        summary = array_slot_summary[slot]
        (top_value, top_prob) = summary['TOPTWO'][0]
        (sec_value, sec_prob) = summary['TOPTWO'][1]
        if top_prob>0 and sec_prob > 0:
            return True, 'select(%s="%s",%s="%s")' % (slot, top_value, slot, sec_value)
        return False, 'null()'


    def getInformByName(self, belief):
        '''
        '''
        global_summary = SummaryMapping.globalSummary(belief, self.domainUtil)
        done = False
        act = 'null()'
        if (global_summary['GLOBAL_BYCONSTRAINTS'] > 0.5 #or global_summary['GLOBAL_BYNAME'] >0 or global_summary['GLOBAL_BYALTERNATIVES'] > 0.5
            ) and\
            global_summary['GLOBAL_COUNT80'] > 3:
            act = DMUtils.getGlobalAction(belief, 'INFORM_BYNAME', self.domainUtil)
        if act != 'null()':
            done = True
        return done, act

    def getInform(self, belief):
        '''
        '''
        act="null()"
        done =False
        global_summary = SummaryMapping.globalSummary(belief, self.domainUtil)
        inform_summary = []
        for num_accepted in range(1, MAX_NUM_ACCEPTED+1):
            inform_summary.append(SummaryMapping.actionSpecificInformSummary(belief, num_accepted, self.domainUtil))
        count80 = global_summary['GLOBAL_COUNT80']
        offer_happened = global_summary['GLOBAL_OFFERHAPPENED']

        if count80 >= MAX_NUM_ACCEPTED:
            count80 = MAX_NUM_ACCEPTED - 1

        arr = inform_summary[count80]
        first = arr[0]  # True if there is no matching entities
        second = arr[1] # True if there is one matching entities
        #third = arr[2]  # True if there is two~four matching entities
        discr = arr[4]  # True if we can discriminate more

        requested_slots = DMUtils.getRequestedSlots(belief)
        #if (first or second or not discr or count80 >= len(Settings.ontology['system_requestable'])) and len(requested_slots)==0:
        act = DMUtils.getInformAction(count80, belief, self.domainUtil)
        if act!="null()":
            done = True
        return [done, act]


    def getInformAlternatives(self, belief):
        '''
        '''
        global_summary = SummaryMapping.globalSummary(belief, self.domainUtil)
        done = False
        act = 'null()'
        if global_summary['GLOBAL_BYALTERNATIVES'] > 0.5:
            act = DMUtils.getGlobalAction(belief, 'INFORM_ALTERNATIVES', self.domainUtil)
        if act != 'null()':
            done = True
        return done, act

    def getInformRequested(self, belief):
        '''
        '''
        global_summary = SummaryMapping.globalSummary(belief, self.domainUtil)
        done = False
        act = 'null()'
        if global_summary['GLOBAL_BYNAME'] > 0.5:
            act = DMUtils.getGlobalAction(belief, 'INFORM_REQUESTED', self.domainUtil)
        if act != 'null()':
            done = True
        return done, act

    def getBye(self, belief):
        '''
        '''
        global_summary = SummaryMapping.globalSummary(belief, self.domainUtil)
        done = False
        act = 'null()'
        if global_summary['GLOBAL_FINISHED'] > 0.5:
            act = DMUtils.getGlobalAction(belief, 'BYE', self.domainUtil)
        if act != 'null()':
            done = True
        return done, act

    def getInformRepeat(self, belief):
        '''
        '''
        global_summary = SummaryMapping.globalSummary(belief, self.domainUtil)
        done = False
        act = 'null()'
        if global_summary['GLOBAL_REPEAT'] > 0.5:
            act = DMUtils.getGlobalAction(belief, 'REPEAT', self.domainUtil)
        if act != 'null()':
            done = True
        return done, act

    def getReqMore(self, belief):
        '''
        '''
        global_summary = SummaryMapping.globalSummary(belief, self.domainUtil)
        done = False
        act = 'null()'
        #if global_summary['GLOBAL_ACK'] > 0.5 or global_summary['GLOBAL_THANKYOU']>0.5:
        act = DMUtils.getGlobalAction(belief, 'REQMORE', self.domainUtil)
        if act != 'null()':
            done = True
        return done, act

    def getRestart(self, belief):
        '''
        '''
        global_summary = SummaryMapping.globalSummary(belief, self.domainUtil)
        done = False
        act = 'null()'
        if global_summary['GLOBAL_RESTART'] > 0.5:
            act = DMUtils.getGlobalAction(belief, 'RESTART', self.domainUtil)
        if act != 'null()':
            done = True
        return done, act

    def Convert(self, belief, action, lastSystemAction):
        '''
        '''
        done = False
        output = ""
        if action == "inform":
            [done, output] = self.getInform(belief)
        elif "request_" in action:
            [done, output]= self.getRequest(belief,action.split("_")[1])
        elif "select_" in action:
            [done, output]= self.getSelect(belief, action.split("_")[1])
        elif "confirm_" in action:
            [done, output]= self.getConfirm(belief,action.split("_")[1])
        elif "inform_byname" in action:
            [done, output]= self.getInformByName(belief)
        elif "inform_alternatives" in action:
            [done, output]= self.getInformAlternatives(belief)
        elif "inform_requested" in action:
            [done, output]= self.getInformRequested(belief)
        elif "bye" in action:
            [done, output]= self.getBye(belief)
        elif "repeat" in action:
            if lastSystemAction != None:
                [done, output]= [True, lastSystemAction]
            else:
                [done, output] = [False, "null()"]
        elif "reqmore" in action:
            [done, output]= self.getReqMore(belief)
        elif "restart" in action:
            [done, output]= self.getRestart(belief)
        else:
            logger.error("Unknown action")
        return output

    def getNonExecutable(self, belief, lastSystemAction):
        '''
        '''
        nonexec = []
        for action in self.action_names:
            if self.Convert(belief, action, lastSystemAction) == "null()":
                nonexec.append(action)
        return nonexec

#END OF FILE
