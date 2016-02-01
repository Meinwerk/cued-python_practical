'''
simulate.py - semantic level user simulator system.
====================================================

Authors: Dongho Kim, David Vandyke  (Copyright CUED Dialogue Systems Group 2015)

**Basic Execution**: 
    >>> python simulate.py [-h] -C CONFIG [-n -r -l -t -g -s]

Optional arguments/flags [default values]::

    -n Number of dialogs [1]
    -r semantic error rate [0]
    -l set the system to use the given policy file for simulation or as learning prior
    -s set random seed 
    -t train the policy
    -g generate text prompts
    -h help

   
**Relevant Config variables** [Default values]::

    [simulate]
    maxturns = 30 
    continuewhensuccessful = False
    forcenullpositive = False
    confscorer = additive

    [hub]
    semo = PassthroughSemO

    [eval]
    successmeasure = objective

.. seealso:: CUED Imports/Dependencies: 

    import :class:`ContextLogger` |.|
    import :class:`Settings` |.|
    import :class:`DMan` |.|
    import :class:`UserSimulator` |.|
    import :class:`SemO` |.|
    import :class:`DomainUtils` |.|
    import :class:`ErrorSimulator`

************************

'''
__author__ = "donghokim, davidvandyke"

import argparse
import numpy as np
import Settings
import DMan
import UserSimulator
import ErrorSimulator
from semo import SemO
import TopicManager
import DomainUtils
import Evaluation
import ContextLogger
try:
       import cPickle as pickle
except:
       import pickle
logger = ContextLogger.getLogger('')


class SimulationSystem:
    '''Semantic level simulated dialog system
    
        :param generate_prompts: (bool) semo output
            
    '''
    def __init__(self, generate_prompts): 
        configs = []
        
        if not Settings.config.has_option("DEFAULT","domains"):
            logger.error("You must specify the domains under the DEFAULT section of the config")
        domains = Settings.config.get("DEFAULT",'domains')
        logger.info('--Simulating dialogues over the domains: ', domains)  
        self.possible_domains = domains.split(',') 
        DomainUtils.checkDomainStrings(domainStrings=self.possible_domains)

        self.maxTurns = 30
        if Settings.config.has_option("simulate", "maxturns"):
            configs.append('maxturns')
            self.maxTurns = Settings.config.getint("simulate", "maxturns") 
        self.forceNullPositive = False
        if Settings.config.has_option("simulate", "forcenullpositive"):
            configs.append('forcenullpositive')
            self.forceNullPositive = Settings.config.getboolean("simulate", "forcenullpositive")
        conf_scorer_name = 'additive'
        if Settings.config.has_option('simulate', 'confscorer'):
            conf_scorer_name = Settings.config.get('simulate', 'confscorer')

        if Settings.config.has_section('simulate'):
            for opt in Settings.config.options('simulate'):
                if opt not in configs and opt not in Settings.config.defaults():
                    logger.error('Invalid config: '+opt)
        
        # [MultiDomain?] Dialogue Management/policy.
        #----------------------------------------- 
        self.topic_manager = TopicManager.TopicManager()
       
        # Simulated User.
        #-----------------------------------------
        # TODO - deal with multi domain simulation - whilst changing Settings.py ill just pass domain here for now
        logger.debug('simulate.py -- XXXXXXX -- directly passing domain name in simulate at present...')
        self.simulator = UserSimulator.SimulatedUsersManager(domainStrings=self.possible_domains)
            
        # Error Simulator.
        #-----------------------------------------
        # TODO - it is a hack for now passing the domain string directly from config via self.possible_domains. look at this
        #self.errorSimulator = ErrorSimulator.CuedErrorSimulator(conf_scorer_name, domainString=self.possible_domains[0])
        self.errorSimulator = ErrorSimulator.SimulatedErrorManager(conf_scorer_name, self.possible_domains)
        
        # SemO.
        #-----------------------------------------
        self.semoClass = None
        if generate_prompts:
            self.semo_name = 'PassthroughSemO'
            if Settings.config.has_option('hub', 'semo'):
                self.semo_name = Settings.config.get('hub', 'semo')
            # SemO.
            if self.semo_name == 'PassthroughSemO':
                self.semoClass = SemO.PassthroughSemO()
            elif self.semo_name == 'BasicSemO':
                self.semoClass = SemO.BasicSemO()
            else:
                logger.warning('Invalid SemO: %s. Using PassthroughSemO.' % self.semo_name)
                self.semoClass = SemO.PassthroughSemO()
        
        # Evaluation Manager.
        #-----------------------------------------
        self.evaluator = Evaluation.EvaluationManager(self.possible_domains)
    
    def set_error_rate(self, r):
        '''Sets the semantic error rate

        :param r: (int) error rate
        :returns: None 
        '''
        self.errorSimulator.set_error_rate(r)

       
    def run(self, episodeNum):
        '''Runs one episode through the simulator
            
        :param None:
        :returns None:

        '''
        sys_act = None
        user_act = ''
        reward = None
        hyps = []
        self.currentDomain = None
        constraints = None # used to conditionally set the belief state of a new domain

        # reset the user simulator:
        self.simulator.restart()

        # reset the dialogue management:
        self.topic_manager.restart()

        # reset the Success evaluator
        self.evaluator.restart()
        
        # determine the number of domains in this dialog > and set maxTurns appropriately
        maxNumTurnsTotal = self.maxTurns * len(self.simulator.using_domains)
        
        for t in range(maxNumTurnsTotal): 
 
            if 'bye(' in user_act:
                break

            print '   Turn %d' % t
            # SYSTEM ACT:
            sys_act = self.topic_manager.act_on(sys_act, hyps, constraints)
            print '    Sys >',
            print sys_act
            # TODO  -- extract turn level features and pass to rnn
            #if self.evaluator.domainEvaluators.[].success_measure == "rnn":
            #    pass
            if t > 0: 
                self.topic_manager.recordReward(reward) 

            if self.semoClass is not None:
                prompt = self.semoClass.generate(sys_act)
                print ' Prompt >', prompt

            #TODO - remove - just debug:
            #if self.currentDomain is not None and previous_domain is not None:
            #    self.topic_manager._print_belief(self.currentDomain)  #TODO - remove - just for debug this line
            
            # USER ACT:
            user_act, user_actsDomain = self.simulator.act_on(sys_act)
            print '   User >', user_act

            # Housecleaning required if we switched domains:
            if self.currentDomain != user_actsDomain: 
                previous_domain = self.currentDomain # this works at start and transitions
                self.currentDomain = user_actsDomain
                sys_act = None
                logger.info('After user_act - domain is now: '+self.currentDomain) 
            else:
                previous_domain = None

            # Confused user act.
            hyps = self.errorSimulator.confuse_act(user_act, self.currentDomain)
            null_prob = 0.0
            for (act, prob) in hyps:
                if act == 'null()':
                    null_prob += prob
                print '   Semi >', act, '[%.6f]' % prob
            
            if self.forceNullPositive and null_prob < 0.001:
                hyps.append(('null()', 0.001))
                print '   Semi > null() [0.001]'

            # Track the topic given the user input information (semantic acts or ASR or whatever features...) 
            # TODO - delete/fix as appropriate
            logger.debug('simulate.py XXXXX -- HACK! ...temporary-pass domain info directly')
            constraints = self.topic_manager.track_topic(domainString=self.currentDomain, 
                                    previousDomainString=previous_domain, episodeNum=episodeNum) 
            #constraints = self.topic_manager.track_topic(userAct=user_act, userAct_hyps=hyps)
            #"""

            # MEASURE REWARD AND SUCCESS
            reward = self.evaluator.reward_and_success(domainString=self.currentDomain, 
                                              um=self.simulator.domainSimulatedUsers[self.currentDomain].um)
            #-------- and perform cleanup/finalisation if we completed previous domain
            if previous_domain is not None: 
                _ = self.evaluator.reward_and_success(domainString=previous_domain, 
                                                  um=self.simulator.domainSimulatedUsers[previous_domain].um)
            #---------------------------------------------------------------------------------------------------------


        # Process ends.
        self.evaluator.finalise_dialog()
        self.topic_manager.endLearningEpisode(domainRewards = self.evaluator.final_rewards) 
        
        # Print dialog summary.       
        self.evaluator.print_dialog_summary()
        return
       

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Simulate')
    parser.add_argument('-C', '--config', help='set config file', required=True, type=argparse.FileType('r'))
    parser.add_argument('-n', '--number', help='set the number of dialogues', type=int)
    parser.add_argument('-r', '--error', help='set error rate', type=int)
    parser.set_defaults(use_color=True)
    parser.add_argument('--nocolor', dest='use_color',action='store_false', help='no color in logging. best to\
                        turn off if dumping to file. Will be overriden by [logging] config setting of "usecolor=".')
    parser.add_argument('-g', '--generate', help='generate text prompts', action='store_true')
    parser.add_argument('-s', '--seed', help='set random seed', type=int)
    args = parser.parse_args()
    if args.error is None:
        args.error = 0
    if args.number is None:
        args.number = 1

    Settings.load_config(args.config.name)
    ContextLogger.createLoggingHandlers(config=Settings.config, use_color=args.use_color)

    Settings.set_seed(args.seed)
        
    simulator = SimulationSystem(args.generate)
    simulator.set_error_rate(float(args.error)/100)
    logger.info('Simulating with error rate: '+str(float(args.error)/100))

    
    for i in range(args.number):
        logger.info('Dialogue %d' % (i+1))
        simulator.run(i) 

    simulator.topic_manager.savePolicy()
    simulator.evaluator.print_summary()


#END OF FILE
