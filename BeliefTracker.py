'''
BeliefTracker.py - Belief Tracker
====================================================

Authors: Dongho Kim, David Vandyke  (Copyright CUED Dialogue Systems Group 2015)

.. seealso:: CUED Imports/Dependencies: 

    import :class:`Settings` |.|
    import :class:`SummaryMapping` |.|
    import :class:`dact` |.|
    import :class:`agentutils` |.|
    import :class:`ContextLogger`


.. warning::
        documentation not complete

************************

'''

__author__="donghokim, davidvandyke"

from collections import defaultdict
import math
import pprint
import copy

import Settings
import SummaryMapping
import dact
import agentutils
import ContextLogger
from practical1_dst.scripts import baseline   #module in belieftracking dir that actually implements the Baseline and Focus trackers (DSTC names)
logger = ContextLogger.getLogger(__name__)  #'belieftracking.BeliefTracker') 


class BeliefTracker(object):
    '''Belief Tracker base class that implements most of the functionality within the dialogue system. The actual inference
    problem of belief tracking (ASR/SLU --> belief state update) is implemented by individual trackers in baseline.py. 
    Hence this class will never be instantiated, it just implements common functionality.'''
    def __init__(self, domainUtil):
        self.prevbelief = None
        self.informedVenueSinceNone = None
        self.turn = 0
        self.domainUtil = domainUtil
        self.CONDITIONAL_BELIEF_PROB = 0.8 # give 0.8 prob mass to slot-vals that occured in prev domains. #TODO config? 

    def str(self):
        return pprint.pformat(agentutils.simplify_belief(self.domainUtil.ontology, self.prevbelief))

    def restart(self):
        self.turn = 0
        self.informedVenueSinceNone = []

    def _convertHypToTurn(self, lastact, obs):
        curturn = {'turn-index': self.turn}

        # Last system action
        slastact = []
        if self.turn > 0:
            slastact = dact.ParseAct(lastact, user=False)
            slastact = agentutils._transformAct(slastact, {}, self.domainUtil.ontology, user=False)
        curturn['output'] = {'dialog-acts': slastact}

        # User act hyps
        accumulated = defaultdict(float)
        for (hyp, prob) in obs:
            hyp = dact.ParseAct(hyp)
            #hyp = agentutils._transformAct(hyp, {}, Settings.ontology)
            hyp = agentutils._transformAct(hyp, {}, self.domainUtil.ontology)
            hyp = dact.inferSlotsForAct(hyp)

            prob = min(1.0, prob)
            if prob < 0:
                prob = math.exp(prob)
            accumulated = agentutils._addprob(accumulated, hyp, prob)
        sluhyps = agentutils._normaliseandsort(accumulated)

        curturn['input'] = {'live': {'asr-hyps':[], 'slu-hyps':sluhyps}}
        return curturn

    def _updateMactFeat(self, last_feature, lastact):
        '''
        Add features into self.prevstate  - recording actions taken by machine
        :return:
        '''
        features = {}
        if self.turn == 0:
            features['lastInformedVenue'] = ''
            features['informedVenueSinceNone'] = []
            features['lastActionInformNone'] = False
            features['offerHappened'] = False

        else:
            last_system_act = dact.ParseAct(lastact, user=False)

            # lastInformedVenue
            current_informed_venue = agentutils._getCurrentInformedVenue(last_system_act)
            if current_informed_venue != '':
                features['lastInformedVenue'] = current_informed_venue
            else:
                features['lastInformedVenue'] = last_feature['lastInformedVenue']

            # informedVenueSinceNone
            if agentutils._hasType(last_system_act, 'canthelp'):
                self.informedVenueSinceNone = []
            if agentutils._hasTypeSlot(last_system_act, 'offer', 'name'):
                venue = agentutils._getTypeSlot(last_system_act, 'offer', 'name')
                self.informedVenueSinceNone.append(venue)
            features['informedVenueSinceNone'] = self.informedVenueSinceNone

            # lastActionInformNone
            if agentutils._hasType(last_system_act, 'canthelp'):
                features['lastActionInformNone'] = True
            else:
                features['lastActionInformNone'] = False

            # offerhappened
            if agentutils._hasTypeSlot(last_system_act, 'offer', 'name'):
                features['offerHappened'] = True
            else:
                features['offerHappened'] = False

        # inform_info
        features['inform_info'] = []
        for numAccepted in range(1,6):
            temp =  SummaryMapping.actionSpecificInformSummary(self.prevbelief, numAccepted, self.domainUtil)
            features['inform_info'] += temp
           
        self.prevbelief['features'] = features

    def input(self, lastact, obs, constraints=None):
        '''Does the actual belief tracking via tracker.addTurn
        '''
        curturn = self._convertHypToTurn(lastact, obs)
        last_feature = None
        if self.prevbelief is not None:
            last_feature = copy.deepcopy(self.prevbelief['features'])
 
        if self.turn == 0:
            self.prevbelief = self.init_belief(constraints)

        track = self.tracker.addTurn(curturn)
        self.prevbelief = self._tobelief(self.prevbelief, track)

        logger.debug(pprint.pformat(curturn))

        self._updateMactFeat(last_feature, lastact)
        self.turn += 1
        logger.debug(self.str())

    def init_belief(self, constraints=None):
        '''Simply constructs the belief state data structure at turn 0
        '''
        belief = {}
        for slot in self.domainUtil.ontology['informable']:
            if slot not in self.domainUtil.ontology['system_requestable']:
                belief[slot] = dict.fromkeys(self.domainUtil.ontology['informable'][slot], 0.0)
            else:
                belief[slot] = dict.fromkeys(self.domainUtil.ontology['informable'][slot]+['dontcare'], 0.0)
            belief[slot]['**NONE**'] = 1.0
        belief['method'] = dict.fromkeys(self.domainUtil.ontology['method'], 0.0)
        belief['method']['none'] = 1.0

        belief['discourseAct'] = dict.fromkeys(self.domainUtil.ontology['discourseAct'], 0.0)
        belief['discourseAct']['none'] = 1.0

        belief['requested'] = dict.fromkeys(self.domainUtil.ontology['requestable'], 0.0)
        if constraints is not None:
            belief = self._conditionally_init_belief(belief,constraints)
        return {'beliefs': belief}


    def _conditionally_init_belief(self,belief,constraints):
        """Method for conditionally setting up the inital belief state of a domain based on information/events that occured
        earlier in the dialogue in ANOTHER (ie different) domain.
        """ 
        # Now initialise the BELIEFS in this domain, based on the determine prior domain constraints
        for slot,valList in constraints.iteritems(): 
            if valList is not None and slot not in ['name']:
                prob_per_val = self.CONDITIONAL_BELIEF_PROB/float(len(set(valList))) 
                for val in valList:
                    belief[slot][val] = prob_per_val
                # and now normalise (plus deal with **NONE**)
                num_zeros = belief[slot].values().count(0.0)  #dont need a -1 for the **NONE** value as not 0 yet
                prob_per_other_val = (1.0-self.CONDITIONAL_BELIEF_PROB)/float(num_zeros)
                for k,v in belief[slot].iteritems():
                    if v == 0.0:
                        belief[slot][k] = prob_per_other_val  #cant think of better way than to loop for this...
                belief[slot]['**NONE**'] = 0.0
        #TODO - delete debug prints: print belief
        #print constraints
        #raw_input("just cond init blief")
        return belief

    def _tobelief(self, prev_belief, track):
        belief = {}
        for slot in self.domainUtil.ontology['informable']:
            if slot in track['goal-labels']:
                if slot not in self.domainUtil.ontology['system_requestable']:
                    belief[slot] = dict.fromkeys(self.domainUtil.ontology['informable'][slot], 0.0)
                else:
                    belief[slot] = dict.fromkeys(self.domainUtil.ontology['informable'][slot]+['dontcare'], 0.0)
                for v in track['goal-labels'][slot]:
                    belief[slot][v] = track['goal-labels'][slot][v]
                belief[slot]['**NONE**'] = 1.0 - sum(belief[slot].values())
            else:
                belief[slot] = prev_belief['beliefs'][slot]

        belief['method'] = dict.fromkeys(self.domainUtil.ontology['method'], 0.0)
        for v in track['method-label']:
            belief['method'][v] = track['method-label'][v]
        belief['discourseAct'] = dict.fromkeys(self.domainUtil.ontology['discourseAct'], 0.0)
        for v in track['discourseAct-labels']:
            belief['discourseAct'][v] = track['discourseAct-labels'][v]
        belief['requested'] = dict.fromkeys(self.domainUtil.ontology['requestable'], 0.0)
        for v in track['requested-slots']:
            belief['requested'][v] = track['requested-slots'][v]

        return {'beliefs': belief}


class BaselineTracker(BeliefTracker):
    """The DSTC *Baseline* tracker. Implemented in /belieftracking/baseline.py
    
    :param domainUtil: (instance) of :class:`DomainUtils`
    """
    def __init__(self, domainUtil):
        super(BaselineTracker, self).__init__(domainUtil) 
        self.tracker = baseline.Tracker()  

    def restart(self):
        super(BaselineTracker, self).restart()
        self.tracker.reset()
        self.turn = 0
 

class FocusTracker(BeliefTracker):
    """The DSTC *Focus* tracker. Implemented in /belieftracking/baseline.py
    
    :param domainUtil: (instance) of :class:`DomainUtils`
    """
    def __init__(self, domainUtil):
        super(FocusTracker, self).__init__(domainUtil)
        self.tracker = baseline.FocusTracker()

    def restart(self):
        super(FocusTracker, self).restart()
        self.tracker.reset()
        self.turn = 0 


class RNNTracker(BeliefTracker):
    '''Note that this hasn't been touched really - APIs etc may need updating for plugging into full dialogue system
    '''
    def __init__(self):
        super(RNNTracker, self).__init__()
        from discriminative import Tracker
        self.tracker = Tracker.createTracker(Settings.config, no_train=True)
        self.tracker.initializeFromConfig()

    def input(self, lastact, obs):
        '''
        Note: this method IS actually different from the 'input' method defined in the base class. (Again, just in passing, as haven't looked to plug in the RNN tracker into the full dialogue system).

        Belief update: b'=tau(b,a,o)
        :param lastact:
        :param obs: [(useracthyp, prob), ...]
        :param isstart:
        :return:
        '''
        last_feature = None
        if self.prevbelief is not None:
            last_feature = copy.deepcopy(self.prevbelief['features'])
        curturn = self._convertHypToTurn(lastact, obs)
        if self.turn == 0:
            self.prevbelief = self.tracker.trackSingleTurn(curturn)
        else:
            self.prevbelief = self.tracker.trackSingleTurn(curturn, self.prevbelief)

        self._updateMactFeat(last_feature, lastact)
        self.turn += 1
        logger.debug(self.str())

#END OF FILE
