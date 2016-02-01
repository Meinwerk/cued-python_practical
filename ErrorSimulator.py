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
ErrorSimulator.py - error simulation 
===============================================

Authors: Dongho Kim, David Vandyke  (Copyright CUED Dialogue Systems Group 2015)

.. seealso:: CUED Imports/Dependencies: 

    import :class:`ConfidenceScorer` |.|
    import :class:`ErrorModel` |.|
    import :class:`DiaAct` |.|
    import :class:`ContextLogger`

************************

''' 
__author__ = "donghokim, davidvandyke"

import ConfidenceScorer
import ErrorModel
import DomainUtils
import DiaAct
import ContextLogger
logger = ContextLogger.getLogger('')


def get_scorer(conf_scorer_name):
    conf_scorer_name = conf_scorer_name.lower()
    logger.info('Confidence scorer: %s' % conf_scorer_name)
    if conf_scorer_name == 'additive':
        conf_scorer = ConfidenceScorer.AdditiveConfidenceScorer(False, False)
    else:
        logger.warning('Invalid confidence scorer: %s. Using additive scorer.' % conf_scorer_name)
        conf_scorer = ConfidenceScorer.AdditiveConfidenceScorer(False, False)
    return conf_scorer


class CuedErrorSimulator():
    def __init__(self, conf_scorer_name, domainString):
        """
        Single domain error simulation module. Operates on semantic acts.
        :param: (str) conf_scorer_name
        :returns None:
        """
        self.em = ErrorModel.EM(domainString)
        self.confScorer = get_scorer(conf_scorer_name)
    
    def set_error_rate(self, r):
        """Sets semantic error rate in :class:`ErrorModel` member

        :param: (int) semantic error rate
        :returns None: 
        """
        self.em.setErrorRate(r)
        
    def confuse_act(self, last_user_act):
        """Clean act in --> Confused act out. 

        :param: (str) simulated users semantic action
        :returns (list) of confused user acts.
        """
        uact = DiaAct.DiaActWithProb(last_user_act)
        n_best = self.em.getNBest(uact)
        n_best = self.confScorer.assignConfScores(n_best)
        
        # Normalise confidence scores
        dSum = 0.0
        for h in n_best:
            dSum += h.P_Au_O
        for h in n_best:
            h.P_Au_O /= dSum
        
        return [(h.to_string(), h.P_Au_O) for h in n_best]


class SimulatedErrorManager():
    def __init__(self, conf_scorer_name, domainStrings):
        """
        """
        #TODO
        self.domainErrorSimulators = dict.fromkeys(DomainUtils.available_domains, None)
        self.using_domains = domainStrings
        for dstring in domainStrings:
            self.domainErrorSimulators[dstring] = CuedErrorSimulator(conf_scorer_name, domainString=dstring) 
        
    def set_error_rate(self, r):
        #TODO
        """Sets semantic error rate in :class:`ErrorModel` member

        :param: (int) semantic error rate
        :returns None: 
        """
        for dstring in self.using_domains:
            self.domainErrorSimulators[dstring].em.setErrorRate(r)
        return
        
    def confuse_act(self, last_user_act, domainString):
        #TODO - needs ammending to know which domain last_user_act is from ... - just pass explictly for now
        """Clean act in --> Confused act out. 

        :param: (str) simulated users semantic action
        :returns (list) of confused user acts.
        """
        return self.domainErrorSimulators[domainString].confuse_act(last_user_act)


#END OF FILE
