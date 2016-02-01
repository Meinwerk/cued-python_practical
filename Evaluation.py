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
Evaluation.py - module for determining dialogue success 
==========================================================================

Author: David Vandyke  (Copyright CUED Dialogue Systems Group 2015)

.. seealso:: CUED Imports/Dependencies: 

    import :class:`DomainUtils` |.|
    import :class:`Settings` |.|
    import :class:`RewardComputer` |.|
    import :class:`ContextLogger` 

************************

'''
__author__ = "djv27"
import numpy as np
import copy
import Settings
import DomainUtils
import RewardComputer
import ContextLogger
logger = ContextLogger.getLogger('')

class DomainEvaluator():
    def __init__(self,domainString):
        """Single domain evaluation module. Responsible for recording/calculating turns, success, reward for a single 
        dialog.
        :param: (str) domain tag
        """
        self.domainString = domainString
        self.successReward = 20
        if Settings.config.has_option("eval", "successreward"):
            configs.append('successreward')
            self.successReward = Settings.config.getint("eval", "successreward")
        self.success_measure = "objective"  # 'objective' or 'rnn'
        if Settings.config.has_option('eval','successmeasure'):
            configs.append('successmeasure')
            self.success_measure = Settings.config.get('eval','successmeasure')
        
        if self.success_measure == "rnn":
            # TODO - also need to consider config and domain dependent settings, like policy_TT etc.
            logger.error("Not integrated into code yet -- also check on use of rewardComputer if using rnn")
            if not Settings.config.has_option('eval','rnnpickle'):  # if using rnn must also give a model to load
                logger.error("When using rnn success prediction you must give model too.")
            import RNN_success # pickle can only load the object if constructor for object is available
            self.load_rnn_model(pickle_file=Settings.config.get('eval','rnnpickle'))
       
        # Reward computer
        self.rewardComputer = RewardComputer.RewardComputer(domainString)
        
        # Recording rew,suc,turn - over all dialogues run during a simulate session
        self.rewards = []
        self.successes = []
        self.turns = []
    
    def restart(self):
        """Reset the domain evaluators variables and reward computer. 
        :param: None
        :returns None:
        """
        self.rewardComputer.restart()
        self.total_reward = 0.0
        self.final_suc = False
        self.final_turns = 0


    def reward_and_success(self, usermodel): 
        """ Updates reward, turns and success for domain dependent evaluation.
        :param: (instance) of :class:`UserModel`
        :returns (int/float): reward for this turn
        """
        # Reward:
        self.get_reward(usermodel=usermodel)
        self.reward = -1  #TODO - note that we always just give -1 each turn atm
        self.total_reward += self.reward
        # Turns:
        self.final_turns += 1
        # Success:
        if self.success_measure == "rnn":
            self.final_suc = self.rnn.predict_success() 
        else:
            self.final_suc = self.get_success()
        return self.reward

    def set_final_reward(self):
        """
        Sets the final reward and total reward, and returns the final reward which is passed to the DMan for learning.
        :param: None
        :returns (int): final reward for dialogue
        """
        if self.final_turns > 0:
            self.final_reward = self.successReward if self.final_suc else 0   
            self.total_reward += self.final_reward  # or: total_rew = final_rew - final_turns + 1
            return self.final_reward
        else:
            return None

    def update_history(self):
        """Records the turns, reward and success for the just completed dialog within the classes history.
        :param: None
        :returns None:
        """
        # Append this dialogs results to dialog history lists if its domain was used in last dialog:
        if self.final_turns > 0: # TODO - any other checks required here?
            self.rewards.append(self.total_reward)
            self.successes.append(self.final_suc)
            self.turns.append(self.final_turns)
        return
 

    def get_reward(self, usermodel):
        '''
        R(s,a,o'). s includes user's goal constraints at s. a is the system action.
        o' includes user action and changed his/her goal requests after performing system action.
        :param: 
        :return:
        '''
        return self.rewardComputer.get_reward(usermodel)

    def get_success(self):
        '''
        :param None:
        :returns: (bool) success indicator, from :class:`RewardComputer` class 
        '''
        return self.rewardComputer.success

    def print_dialog_summary(self):
        """
        """
        if self.final_turns > 0:
            logger.info("Evaluation of domain: "+self.domainString)
            print '   rew = %d, suc = %d, turn = %d' % (self.total_reward, self.final_suc, self.final_turns)
            print ''
        return

    def print_summary(self):
        """
        Prints the summary of a run of simulate.py - ie multiple dialogs
        """
        num_dialogs = len(self.rewards)
        assert(len(self.successes)==num_dialogs)
        assert(len(self.turns)==num_dialogs)
        print '-'*20
        print "Results for domain: "+self.domainString
        logger.info('# of dialogues  = %d' % num_dialogs)
        if num_dialogs:
            logger.info('Average reward  = %.2f +- %.2f' % (np.mean(self.rewards),\
                                                            1.96 * np.std(self.rewards) / np.sqrt(num_dialogs)))
            logger.info('Average success = %.2f +- %.2f' % (np.mean(self.successes)*100,
                                                            1.96 * 100 * np.std(self.successes) / np.sqrt(num_dialogs)))
            logger.info('Average turns   = %.2f +- %.2f' % (np.mean(self.turns), \
                                                            1.96 * np.std(self.turns) / np.sqrt(num_dialogs)))
        return


    def load_rnn_model(self,pickle_file):
        ''' 
            .. Todo::
                Haven't yet integrated RNN success predictor into code
        '''
        logger.debug("loading the rnn success predictor pickle...")
        with open(pickle_file,'r') as pfile:
            self.rnn = pickle.load(pfile)
 

class EvaluationManager():
    def __init__(self,domainStrings):
        """
        """
        self.using_domains = copy.copy(domainStrings)
        self.domainEvaluators = dict.fromkeys(DomainUtils.available_domains, None)
        for dstring in domainStrings:
            self.domainEvaluators[dstring] = DomainEvaluator(dstring)

    def restart(self):
        """
        """
        for dstring in self.using_domains:
            self.domainEvaluators[dstring].restart()

    def reward_and_success(self,domainString, um):
        """
        """
        # TODO - again, assume only one domain running at once. passing back an int for reward. -- should be vector
        # or something if multiple domains to run at once. 
        reward = self.domainEvaluators[domainString].reward_and_success(usermodel=um)
        return reward

    def finalise_dialog(self):
        """First calls :classmethod:`domain_rewards` which sets the final reward based on the success (which is determined by the evaluation method earlier) - this creates a vector of rewards over the available domains. Second and finally, calls the domains :classmethod:`update_history` which records the turns,reward,success.

        :param None:
        :returns: None
        """
        self.domain_rewards()
        self.update_history()

    def update_history(self):
        for dstring in self.using_domains:
            self.domainEvaluators[dstring].update_history()
        return

    def domain_rewards(self):
        """
        """
        self.final_rewards = dict.fromkeys(DomainUtils.available_domains, None)
        for dstring in self.using_domains:
            self.final_rewards[dstring] = self.domainEvaluators[dstring].set_final_reward()
        return

    def print_dialog_summary(self):
        """
        Prints the history of the just completed dialog.
        """
        for dstring in self.using_domains:
            self.domainEvaluators[dstring].print_dialog_summary()

    def print_summary(self):
        """
        Prints the history over all dialogs run thru simulate.
        """
        for dstring in self.using_domains:
            self.domainEvaluators[dstring].print_summary()

#END OF FILE
