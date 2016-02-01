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
ErrorModel.py - error simulation 
===============================================

Authors: Dongho Kim, David Vandyke  (Copyright CUED Dialogue Systems Group 2015)

 
**Relevant Config variables** [Default values]::

    [em]
    nbestsize = 1 
    confusionmodel = RandomConfusions
    nbestgeneratormodel = UniformNBestGenerator

.. seealso:: CUED Imports/Dependencies: 

    import :class:`ConfusionModel` |.|
    import :class:`NBestGenerator` |.|
    import :class:`Settings` |.|
    import :class:`ContextLogger`

************************

''' 
__author__="donghokim, davidvandyke"
import ConfusionModel
import NBestGenerator
import Settings
import ContextLogger
logger = ContextLogger.getLogger('')


class EM():
    '''
    Main class for error simulation

    :param None:
    '''
    def __init__(self, domainString):
        configs = []
        self.nBestSize = 1
        if Settings.config.has_option('em', 'nbestsize'):
            configs.append('nbestsize')
            self.nBestSize = Settings.config.getint('em','nbestsize')
        self.confusionModelName = 'RandomConfusions'
        if Settings.config.has_option('em','confusionmodel'):
            configs.append('confusionmodel')
            self.confusionModelName = Settings.config.get('em','confusionmodel')
        self.nBestGeneratorName = 'UniformNBestGenerator'
        if Settings.config.has_option('em','nbestgeneratormodel'):
            configs.append('nbestgeneratormodel')
            self.nBestGeneratorName = Settings.config.get('em','nbestgeneratormodel')
        
        logger.info('N-best list size: '+str(self.nBestSize))
        logger.info('N-best generator model: '+self.nBestGeneratorName)
        logger.info('Confusion model: '+self.confusionModelName)

        if Settings.config.has_section('em'):
            for opt in Settings.config.options('em'):
                if opt not in configs and opt not in Settings.config.defaults():
                    logger.error('Invalid config: '+opt)

        # Create confusion model.
        if self.confusionModelName == 'RandomConfusions':
            self.confusionModel = ConfusionModel.EMRandomConfusionModel(domainString)
        else:
            logger.error('Confusion model '+self.confusionModelName+' is not implemented.')
        
        # Create N-best generator.
        if self.nBestGeneratorName == 'UniformNBestGenerator':
            self.nBestGenerator = NBestGenerator.EMNBestGenerator(self.confusionModel, self.nBestSize)
        elif self.nBestGeneratorName == 'SampledNBestGenerator':
            logger.warning('Note that the original C++ implementation of EMSampledNBestGenerator was actually the same to EMUniformNBestGenerator.')
            logger.warning('Here the size of N-best list is also sampled from uniform distribution of [1,..,N].')
            self.nBestGenerator = NBestGenerator.EMSampledNBestGenerator(self.confusionModel, self.nBestSize)
        else:
            logger.error('N-best generator '+self.nBestGeneratorName+' is not implemented.')
     
    def setErrorRate(self, err):
        '''
        :param err: (int) error rate
        :returns: None
        '''
        self.nBestGenerator.set_error_rate(err)
        self.errorRate = err
    
    def getNBest(self, a_u):
        '''
        Returns a list of simulated semantic hypotheses given the true act a_u

        :param a_u: (str)
        :returns: (instance) 
        '''
        return self.nBestGenerator.getNBest(a_u)




# END OF FILE
