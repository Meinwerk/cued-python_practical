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
NBestGenerator.py - 
====================================================

Author: Dongho Kim  (Copyright CUED Dialogue Systems Group 2015)

.. seealso:: CUED Imports/Dependencies: 

    import :class:`Settings` |.|
    import :class:`ContextLogger`

************************

'''
import copy

import Settings
import ContextLogger
logger = ContextLogger.getLogger('')


class NBestGenerator(object):
    def __new__(cls, confusion_model, nbest_size):
        new = object.__new__(cls)
        new.confusionModel = confusion_model
        new.error_rate = None
        new.nbest_size = nbest_size
        return new

    def set_error_rate(self, error_rate):
        self.error_rate = error_rate


class EMNBestGenerator(NBestGenerator):
    '''
    Tool for generating random semantic errors.
    '''
    def getNBest(self, a_u):
        '''
        Returns an N-best list of dialogue acts of length nbest_size.
        Each entry is a random confusion of the given dialogue act a_u with probability e (errorRate).
        
        :param a_u: (instance) of :class:`DiaActWithProb`
        '''
        if self.error_rate is None:
            logger.error('Error rate is not specified. Call set_error_rate first.')

        n_best = []
        for i in range(self.nbest_size):
            if Settings.random.rand() < self.error_rate:
                # Creating wrong hyp.
                confused_a_u = self.confusionModel.create_wrong_hyp(a_u)
                confused_a_u.P_Au_O = 1./self.nbest_size
                n_best.append(confused_a_u)
            else:
                a_u_copy = copy.deepcopy(a_u)
                a_u_copy.P_Au_O = 1./self.nbest_size
                n_best.append(a_u_copy)
        return n_best


class EMSampledNBestGenerator(NBestGenerator):
    '''
    The Dirichlet collection NBest generator operates by sampling a length for the N-best list and then
    sampling from a specific Dirichlet for that length.

    This is a derived class from base :class:`NBestGenerator`

    :param confusion_model: (instance) of :class:`ConfusionModel`
    :param nbest_size: (int)

    .. note:: The original C++ implementation did not sample N which is the length of the N-best list.
    '''
    def __init__(self, confusion_model, nbest_size):
        self.confidence = [1./nbest_size] * nbest_size

    def getNBest(self, a_u):
        '''
        :param a_u: (instance) of :class:`DiaActWithProb`
        :returns: (list) of such dialogue act types as input
        '''
        if self.error_rate is None:
            logger.error('Error rate is not specified. Call set_error_rate first.')

        n_best = []
        size = Settings.random.choice(range(1, self.nbest_size+1))
        for i in range(size):
            if Settings.random.rand() < self.error_rate:
                new_hyp = self.confusionModel.create_wrong_hyp(a_u)
            else:
                new_hyp = copy.deepcopy(a_u)
            new_hyp.P_Au_O = 1./size
            n_best.append(new_hyp)
        return n_best

#END OF FILE
