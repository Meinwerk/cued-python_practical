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
texthub.py - text level dialog system.
====================================================

Authors: Dongho Kim, David Vandyke  (Copyright CUED Dialogue Systems Group 2015)

**Basic Execution**:
    >>> python texthub.py [-h] -C CONFIG [-l -r]

Optional arguments/flags [default values]::

    -r semantic error rate [0]
    -l set the system to use the given policy file
    -h help


**Relevant config variables**  (values are defaults)::

    [hub]
    semi = PassthroughSemI
    semo = PassthroughSemO


.. seealso:: CUED Imports/Dependencies: 

    import :class:`ContextLogger` |.|
    import :class:`Settings` |.|
    import :class:`DMan` |.|
    import :class:`SemI` |.|
    import :class:`SemO`

.. Note::
            Assumes use of RNN tracker (whose input is ASR), meaning there is no semantic parser. PassthroughSemI can be used with the focus tracker: text inputs should then be semantic acts, e.g. inform(area=south)

************************

'''

__author__ = "donghokim, davidvandyke"

import argparse

import ContextLogger
import Settings
import DomainUtils
import DMan
import TopicManager
from semi import SemI
from semo import SemO
logger = ContextLogger.getLogger('')


class ConsoleHub():
    '''text based dialog system

        :param None:
    '''
    def __init__(self):
       
        if not Settings.config.has_option("DEFAULT","domains"):
            logger.error("You must specify the domains under the DEFAULT section of the config")
        domains = Settings.config.get("DEFAULT",'domains')
        logger.info('--Dialogues over the domains: ', domains)  

        configlist = []
        #TODO - delete - deprecated
        """
        self.semi_name = 'PassthroughSemI'
        if Settings.config.has_option('hub', 'semi'):
            configlist.append('semi')
            self.semi_name = Settings.config.get('hub', 'semi')
        """
        self.semo_name = 'PassthroughSemO'
        if Settings.config.has_option('hub', 'semo'):
            configlist.append('semo')
            self.semo_name = Settings.config.get('hub', 'semo')

        if Settings.config.has_section('hub'):
            for opt in Settings.config.options('hub'):
                if opt not in configlist and opt not in Settings.config.defaults():
                    logger.error('Invalid config: ' + opt)

        # [MultiDomain?] Dialogue Management/policy.
        #----------------------------------------- 
        self.topic_manager = TopicManager.TopicManager()

        #TODO - del: Policy.
        # del: self.system = DMan.DMan(policyFileName)

        # SemI.
        self.semi = SemI.SemIManager()

        # SemO.
        if self.semo_name == 'PassthroughSemO':
            self.semo = SemO.PassthroughSemO()
        elif self.semo_name == 'BasicSemO':
            self.semo = SemO.BasicSemO()
        else:
            logger.warning('Invalid SemO: %s. Using PassthroughSemO.' % self.semo_name)
            self.semo = SemO.PassthroughSemO()

    def run(self):
        '''
        Runs one episode through Hub

        :param None:
        :returns: None
        '''
        lastSysAct = None
        lastHyps = []
        self.topic_manager.restart()
        self.currentDomain = None

        t = 0
        while True:
            print ''
            print 'Turn', t
            # TODO del: lastSysAct = self.system.act_on(lastSysAct, lastHyps)
            lastSysAct = self.topic_manager.act_on(lastSysAct, lastHyps)
            print 'Sys    >', lastSysAct

            prompt = self.semo.generate(lastSysAct)
            print 'Prompt >', prompt

            if 'bye(' in lastSysAct:
                return

            # User act.
            obs = raw_input('User   > ')
            if t == 0 and 'switch("' not in obs:
                msg = 'Currently, you should start by saying which domain to switch to. Enter exactly on '
                msg +=      'first turn (where DOMAINTAG is TT,TSB6 etc): switch("DOMAINTAG")'
                exit(msg)

            lastHyps,user_actsDomain = self.semi.texthub_decode([(obs, 1.0)]) #separate func to keep simulate simple 
            print 'SemI   >', lastHyps

            # Which domain - depends on semi decoder - if topic tracker is "cheating"
            if user_actsDomain is not None:
                if user_actsDomain in DomainUtils.available_domains:
                    # then switching
                    self.currentDomain = user_actsDomain
                    lastSysAct = None
 
            if len(lastHyps) > 0 and 'bye(' in lastHyps[0][0]:
                return
            # Confused user act.
            # lastHyps = self.errorSimulator.confuseAct(lastUserAct)
            # print 'lastHyps >', lastHyps
            # nullProb = 0.0
            # for (act, prob) in lastHyps:
            #     if act == 'null()':
            #         nullProb += prob
            #     print 'Semi >', act, '['+str(prob)+']'

            # if self.forceNullPositive and nullProb < 0.001:
            #     lastHyps.append(('null()',0.001))
            #     print 'Semi > null() [0.001]'
            #--------------------------------

            # Track the topic given the user input information (semantic acts or ASR or whatever features...) 
            # TODO - delete/fix as appropriate
            logger.debug('simulate.py XXXXX -- HACK! ...temporary-pass domain info directly')
            self.topic_manager.track_topic(domainString=self.currentDomain) 
            #self.topic_manager.track_topic(userAct=user_act, userAct_hyps=hyps)
            #"""

            t += 1

        # Process ends.

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='TextHub')
    parser.add_argument('-C', '--config', help='set config file', required=True, type=argparse.FileType('r'))
    parser.add_argument('-s', '--seed', help='set random seed', type=int)
    args = parser.parse_args()

    Settings.load_config(args.config.name)
    ContextLogger.createLoggingHandlers(Settings.config)

    Settings.set_seed(args.seed)

    hub = ConsoleHub()
    hub.run()


#END OF FILE
