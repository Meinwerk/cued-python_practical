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
DMan.py - Dialogue manager
====================================================

Authors: Dongho Kim, David Vandyke  (Copyright CUED Dialogue Systems Group 2015)

**Basic Usage**: 
    >>> import DMan
    >>> system = DMan.DMan(policy_filename, train)

**Parameters**:
    *policy_filename* (str) : policy file for dialogue manager. |.|
    *train* (bool) : indicating whether the given policy will be trained or not.

.. seealso:: CUED Imports/Dependencies: 

    import :class:`Settings` |.|
    import :class:`BeliefTracker` |.|
    from :class:`policy` import :meth:`SummaryAction` |.|
    import :class:`ContextLogger`

************************

'''
__author__="donghokim, davidvandyke"

import Settings
import BeliefTracker
import DomainUtils
from policy import SummaryAction

import ContextLogger
logger = ContextLogger.getLogger('')


class DMan:
    '''Dialogue manager: controls all policy type/instance and policy learning choices. 
    '''
    def __init__(self,domainUtil): 
        """
        Constructor for Dialogue manager: has a belief state tracker and a policy.
        :param domainUtil: (instance) of :class:`DomainUtils`
        :return:
        """
        configlist = ['policytype']
        self.useconfreq = False
        self.actions = SummaryAction.SummaryAction(domainUtil)
        self.bcm = False
        self.curr_policy = -1
        #TODO adding domainUtil instance to class - for conditional tracking -- may not really be required
        self.domainUtil = domainUtil 

        # General [policy] config options. (just bcm at present, rest use a domain tag as well)
        if Settings.config.has_option('policy', 'bcm'):
            configlist.append('bcm')
            self.bcm = Settings.config.getboolean('policy', 'bcm')

        if not Settings.config.has_section('policy_'+domainUtil.domainString):
            logger.warning("No policy section specified for domain: "+domainUtil.domainString+" - defaulting to HDC")
            self.pol_type = 'hdc'

        self.learning = False
        if Settings.config.has_option('policy_'+domainUtil.domainString, 'learning'):
            configlist.append('learning')
            self.learning = Settings.config.getboolean('policy_'+domainUtil.domainString, 'learning')
        if Settings.config.has_option('policy_'+domainUtil.domainString, 'useconfreq'):
            configlist.append('useconfreq')
            self.useconfreq = Settings.config.getboolean('policy_'+domainUtil.domainString, 'useconfreq')
        if Settings.config.has_option('policy_'+domainUtil.domainString, "currpolicy"):
            configs.append('currpolicy')
            self.curr_policy = Settings.config.getint('policy_'+domainUtil.domainString,"currpolicy")

        in_policy_file = None
        if Settings.config.has_option('policy_'+domainUtil.domainString, 'inpolicyfile'):
            configlist.append('inpolicyfile')
            in_policy_file = Settings.config.get('policy_'+domainUtil.domainString, 'inpolicyfile')

        out_policy_file = None
        if Settings.config.has_option('policy_'+domainUtil.domainString, 'outpolicyfile'):
            configlist.append('outpolicyfile')
            out_policy_file = Settings.config.get('policy_'+domainUtil.domainString, 'outpolicyfile')

        if in_policy_file is None:
            self.pol_type = 'hdc'
        else:
            self.pol_type = "gp"
            if Settings.config.has_option('policy_'+domainUtil.domainString, 'policytype'):
                self.pol_type = Settings.config.get('policy_'+domainUtil.domainString, 'policytype')
            if self.pol_type == 'hdc':
                logger.warning('Policy file is given: %s, but policy type is set to hdc.')
                logger.warning('Ignoring the given policy file and using hdc policy.')

        if self.pol_type == 'hdc':
            from policy import HDCPolicy
            self.policy = HDCPolicy.HDCPolicy(use_confreq=self.useconfreq,
                                              domainUtil=domainUtil )
        elif self.pol_type == 'gp':
            from policy import GPPolicy
            if self.bcm :
                policy_files = DomainUtils.get_all_policies()   # TODO - delete - deprecated -- policy_file.split(";")
                self.policies = []
                for pf in policy_files:
                    self.policies.append(GPPolicy.GPPolicy(pf, len(self.actions.action_names), self.actions.action_names))
            else: 
                self.policy = GPPolicy.GPPolicy(in_policy_file, 
                                                out_policy_file,
                                                len(self.actions.action_names), 
                                                self.actions.action_names, 
                                                domainUtil,
                                                self.learning)
        elif self.pol_type == 'mcc':
            from policy import MCCPolicy
            self.policy = MCCPolicy.MCCPolicy(
                                            in_policy_file, 
                                            out_policy_file, 
                                            self.useconfreq, 
                                            self.learning, 
                                            domainUtil )


        #------------------------------ 
        # TODO - following policies need to receive the DomainUtils instance that Policy.Policy() requires
        # --- Not currently implemented as we aren't currently using these policy types 
        elif True:
            exit('NOT IMPLEMENTED... see msg at this point in code')
        elif self.pol_type == 'type':
            from policy import TypePolicy
            self.policy = TypePolicy.TypePolicy()
        elif self.pol_type == 'select':
            from policy import SelectPolicy
            self.policy = SelectPolicy.SelectPolicy(use_confreq=self.useconfreq)
        elif self.pol_type == 'nn':
            from policy import NNPolicy
            # TODO - further change here - train is now implmented in config file. below needs updating 
            self.policy = NNPolicy.NNPolicy(use_confreq=self.useconfreq, is_training=train)
        else:
            logger.error('Invalid policy type: ' + self.pol_type)
        #------------------------------

        if self.pol_type != 'gp' and self.pol_type != 'hdc' and self.pol_type != 'mcc':
            self.policy.load(policy_file)

        belief_type = 'baseline' # can alternatively use 'focus' as the default
        if Settings.config.has_option('policy_'+domainUtil.domainString, 'belieftype'):
            configlist.append('belieftype')
            belief_type = Settings.config.get('policy_'+domainUtil.domainString, 'belieftype')

        self.startwithhello = False
        if Settings.config.has_option('policy_'+domainUtil.domainString, 'startwithhello'):
            configlist.append('startwithhello')
            self.startwithhello = Settings.config.getboolean('policy_'+domainUtil.domainString, 'startwithhello')

        if Settings.config.has_section('policy_'+domainUtil.domainString):
            for opt in Settings.config.options('policy_'+domainUtil.domainString):
                if opt not in configlist and opt not in Settings.config.defaults():
                    logger.error('Invalid config: '+opt)

        if belief_type == 'focus':
            self.beliefs = BeliefTracker.FocusTracker(domainUtil)
        elif belief_type == 'baseline':
            self.beliefs = BeliefTracker.BaselineTracker(domainUtil)
        elif belief_type == 'rnn':
            self.beliefs = BeliefTracker.RNNTracker()
        else:
            logger.error('Invalid belief tracker: ' + belief_type)

    def restart(self):
        '''resets the belief state by calling the restart() method of the  tracker being used.
        
            :param: None
            :returns: None
        ''' 
        self.beliefs.restart()
        return

    def act_on(self, lastSysAct, inputActs, constraints=None):
        '''
        :param lastSysAct: last system action
        :param inputActs: semantic hypotheses
        :returns: (str) dialogue  act
        '''
        # At the very first turn,
        self.summaryAct = None
        self.lastSystemAction = None
        self.beliefs.input(lastSysAct, inputActs, constraints) 
        if lastSysAct is None and self.startwithhello:
            return 'hello()'
        act =  self._actOn()
        return act

    def bayesianCommitteeDecision(self, nonExecutableActions):
        '''
        :param nonExecutableActions: 
        :returns: None (sets self.summaryAct)
        '''
        values = []
        for policy in self.policies:
            values.append(policy.getValue(self.beliefs.prevbelief, nonExecutableActions))

        final = values[0]

        for k in range(len(final)):
            priorVar = self.policies[0].getPriorVar(self.beliefs.prevbelief, final[k][0])
            assert(final[k][1][1]>0)
            final[k][1][0] /= final[k][1][1]
            final[k][1][1] = 1.0/final[k][1][1]
            assert(priorVar>0)
            final[k][0][0] += -float(len(values)-1)/priorVar

        for i in range(len(values)):
            if i==0:
                continue
            for k in range(len(values[i])):
                assert(final[k][0] == values[i][k][0])
                assert( values[i][k][1][1] > 0)
                final[k][1][0] += values[i][k][1][0]/values[i][k][1][1]
                final[k][1][1] += 1.0/values[i][k][1][1]

        for k in range(final):
            assert (final[k][1][1] > 0)
            final[k][1][1] = 1.0/final[k][1][1]
            final[k][1][0] *= final[k][1][1]

        maxVal = final[0][1][0]
        self.summaryAct = final[0][0]

        for k in range(len(final)):
            elem = [final[k][0], 0]

            if final[k][1][1] > 0:
                elem[1] = sqrt(final[k][1][1]) * np.random.randn() + final[k][1][0]
            if elem[1] > maxVal:
                self.summaryAct = elem[0]
                maxVal = elem[1]

    def _actOn(self):
        if self.pol_type == "hdc":
            systemAct = self.policy.work(self.beliefs.prevbelief)
        elif self.pol_type == 'gp':

            nonExecutableActions = self.actions.getNonExecutable(self.beliefs.prevbelief, self.lastSystemAction)

            if self.bcm:
                self.bayesianCommitteeDecision(nonExecutableActions)
            else:
                self.summaryAct = self.policy.nextAction(self.beliefs.prevbelief,nonExecutableActions)

            if type(self.summaryAct) == int:
                self.summaryAct = self.actions.action_names[self.summaryAct]

            systemAct = self.actions.Convert(self.beliefs.prevbelief,self.summaryAct,self.lastSystemAction)
            self.lastSystemAction = systemAct

        elif self.pol_type == 'mcc':
            self.summaryActName, self.summaryAct = self.policy.select(self.beliefs.prevbelief, self.actions.action_names, self.actions, self.lastSystemAction)
            systemAct = self.actions.Convert(self.beliefs.prevbelief,self.summaryActName,self.lastSystemAction)
            self.lastSystemAction = systemAct
        
        else:
            logger.error('Currently unhandled policy type...'+self.pol_type) # should never get here, will have been checked.
        return systemAct

    def startLearningEpisode(self, episodeNum):
        '''Calls selected policies startLearningEpisode() method.
            
            :param: None
            :returns: None
        '''
        if not self.learning:
            return
        if self.pol_type in ('gp', 'mcc'):
            if self.bcm and self.pol_type == 'gp':
                for policy in self.policies:
                    policy.startLearningEpisode()
            elif self.pol_type == 'gp':
                self.policy.startLearningEpisode()
            else: # mcc policy, need episodeNum info for annealing epsilon
                self.policy.startLearningEpisode(episodeNum)
        else:
            logger.warning('startLeaningEpisode is not implemented yet, or not applicable (ie HDC policy)')

    def recordReward(self, reward):
        '''Records the reward (along with previous beliefs and system summary act) thru selected policies \
                recordExecutedAction() method.

            :param reward: (int) turn reward
            :returns: None
        '''
        if self.pol_type == 'hdc':
            return
        elif self.pol_type in ('gp','mcc') and self.summaryAct != None:
            if self.bcm and self.pol_type == 'gp':
                for policy in range(self.policies):
                    policy.recordExecutedAction(self.beliefs.prevbelief, self.summaryAct, reward)
            else:
                self.policy.recordExecutedAction(self.beliefs.prevbelief, self.summaryAct, reward)
        else:
            logger.warning('recordReward is not implemented yet.')

    def savePolicy(self):
        '''Saves policy (policies)

            :param: None
            :returns: None
        '''
        if not self.learning:
            return
        if self.pol_type == 'hdc':
            logger.warning('Cant save handcrafted policy')
            return
        elif self.pol_type in ('gp', 'mcc'):
            if self.bcm and self.pol_type == 'gp':
                for policy in self.policies:
                    policy.savePolicy()
            else:
                self.policy.savePolicy()
        else:
            logger('savePolicy is not implemented yet')

    def endLearningEpisode(self, reward):
        '''Executes endLearningEpisode() method of the selected policy

            :param reward: (int) reward
            :returns: None
        '''
        if not self.learning:
            return
        if self.pol_type == 'hdc':
            return
        elif self.pol_type in ('gp', 'mcc'):
            if self.bcm and self.pol_type == 'gp':
                if self.curr_policy>=0 and self.curr_policy<len(self.policies):
                    self.policies[self.curr_policy].recordExecutedAction(self.beliefs.prevbelief, self.summaryAct, reward)
                    self.policies[self.curr_policy].endLearningEpisode()
                else:
                    logger.error("Current policy out of range "+str(self.curr_policy))
            else:
                self.policy.recordExecutedAction(self.beliefs.prevbelief, self.summaryAct, reward)
                self.policy.endLearningEpisode()
        else:
            logger.warning('endLearningEpisode is not implemented yet.')

    def getBelief80_pairs(self):
        """Called by EXITING DOMAIN
        """
        pairs = {}
        for slot in self.domainUtil.ontology["system_requestable"]:
            maxval = max(self.beliefs.prevbelief["beliefs"][slot].values())
            maxindex = self.beliefs.prevbelief["beliefs"][slot].values().index(maxval)
            maxvalsKEY = self.beliefs.prevbelief["beliefs"][slot].keys()[maxindex]
            if maxval > 0.80 and maxvalsKEY not in ['dontcare','none','**NONE**']:
                pairs[slot] = maxvalsKEY
        return pairs

    def get_conditional_constraints(self,prev_domain_constraints):
        """Called by ENTERING DOMAIN
        Takes a dict (keys=all available domains we have -- more info this way than just a list of 
        slots + values) of constraints from previous domains AS DETERMINED BY THE DIALOGS IN THOSE 
        DOMAINS WITH THE DOMAINS OWN TRACKER - then conditionally initialises the new tracker. 
        (Meaning this is only called when domain is first launched within a single dialog).

        :param prev_domain_constraints:
        :returns None:
        """
        #TODO -- in order to infer how other domain constraints (slotX=valueY) affect this domain, should potentially
        # ------ just be passing the entire prev_domain_constraints thru to tracker...
        constraints = dict.fromkeys(self.domainUtil.ontology["system_requestable"])
        informable_vals = self.domainUtil.ontology["informable"]
        for dstring in prev_domain_constraints: 
            if prev_domain_constraints[dstring] is not None:
                # is then a dict with the constraints from that domain. keys=slots, values=VALUE-FROM-SLOT
                for slot,val in prev_domain_constraints[dstring].iteritems():
                    if slot in constraints.keys():
                        if val in informable_vals[slot]: 
                            if constraints[slot] is None:
                                constraints[slot] = [val]
                            else:
                                constraints[slot].append(val)
        logger.debug("Constraints: "+str(constraints))
        return constraints

if __name__ == '__main__':
    raw_input('THE MAIN PART of this file needs changing since multi domain changes')
    import argparse
    from rlglue.agent.Agent import Agent
    from rlglue.agent import AgentLoader as AgentLoader
    from rlglue.types import Action
    from rlglue.utils import TaskSpecVRLGLUE3

    parser = argparse.ArgumentParser(description='DMan')
    parser.add_argument('-C', '--config', help='set config file')
    parser.add_argument('-l', '--policy', help='set the system to learn and use the given policy file (handcrafted if not specified)')
    parser.add_argument('-t', '--train', help='train the policy', action='store_true')
    args = parser.parse_args()

    Settings.load_config(args.config)
    ContextLogger.createLoggingHandlers(Settings.config)

    class DManAgent(Agent):
        def __init__(self, policy_file, train):
            self.dman = DMan(policy_file, train)
            self.last_sys_act = None

        def agent_init(self, taskSpecString):
            taskSpec = TaskSpecVRLGLUE3.TaskSpecParser(taskSpecString)
            if taskSpec.valid:
                logger.info('TaskSpec parsed: '+taskSpecString)
            else:
                logger.info('TaskSpec could not be parsed: '+taskSpecString)

            # self.lastAction = Action()
            # self.lastAction.charArray = list('null()')
            # self.lastObservation = Observation()
            # self.last_sys_act = None
            # self.dman.restart()

        def agent_start(self, observation):
            self.last_sys_act = None
            self.dman.restart()
            hypstr = ''.join(observation.charArray)
            hyplist = hypstr.split('\t')
            hyp_prob_list = [(hyplist[i], observation.doubleArray[i]) for i in range(len(hyplist))]
            self.last_sys_act = self.dman.act_on(self.last_sys_act, hyp_prob_list)

            return_act = Action()
            return_act.charArray = list(self.last_sys_act.encode('ascii', 'replace'))
            return return_act

        def agent_step(self, reward, observation):
            hypstr = ''.join(observation.charArray)
            hyplist = hypstr.split('\t')
            hyp_prob_list = [(hyplist[i], observation.doubleArray[i]) for i in range(len(hyplist))]
            self.last_sys_act = self.dman.act_on(self.last_sys_act, hyp_prob_list)
            self.dman.train(reward)

            return_act = Action()
            return_act.charArray = list(self.last_sys_act.encode('ascii', 'replace'))
            return return_act

        def agent_end(self, reward):
            self.dman.train(reward)
            self.dman.end_episode(reward)

        def agent_cleanup(self):
            pass

        def agent_message(self, message):
            pass

    AgentLoader.loadAgent(DManAgent(args.policy, args.train))

#END OF FILE
