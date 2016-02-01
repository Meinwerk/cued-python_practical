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
NNPolicy.py - Neural Net policy
====================================================

Author: Dongho Kim  (Copyright CUED Dialogue Systems Group 2015)

.. seealso:: CUED Imports/Dependencies: 

    import :class:`Policy` |.|
    import :class:`DMUtils` |.|
    import :class:`SummaryMapping` |.|
    import :class:`Settings` |.|
    import :class:`ContextLogger`
 
.. warning::        
        **NOT FUNCTIONAL** - imports from discriminative are currently commented out simply to build the sphinx doc page. 
        discriminative refers to Matt's RNN code, which is not part of this repo but can possibly be linked to via a soft link to the location within the orginal C++ code. 


.. warning::
        Documentation not done. 

************************

'''


import json
import pickle
import os

# Belief tracker
from collections import defaultdict
#from discriminative import Tracker

# MLP policy
#from discriminative import Models
#from discriminative import SGD
import numpy as np

import Policy
import Settings
import ContextLogger
logger = ContextLogger.getLogger(__name__)


class NNPolicy(Policy.Policy):
    def __init__(self, use_confreq=True, is_training=False, domainUtil=None):
        super(NNPolicy, self).__init__(use_confreq, domainUtil)
        self.is_training = is_training
        # inherits from policy() self.domainUtil -- which accesses ontology and db for domain
        raw_input("--NOTE!!!! -- NNPolicy has not been run since Settings.ontology usage removed ... so test/tread carefully")

        '''
        Initialise NN policy structure.
        '''
        self.gamma = 1.0
        if Settings.config.has_option('nnpolicy', 'gamma'):
            self.gamma = Settings.config.getfloat('nnpolicy', 'gamma')
        self.policy_hidden_structure = []
        if Settings.config.has_option("nnpolicy", "hidden_structure"):
            self.policy_hidden_structure = json.loads(Settings.config.get("nnpolicy", "hidden_structure"))
        self.regulariser = 0.0
        if Settings.config.has_option('nnpolicy', 'regulariser'):
            self.regulariser = Settings.config.getfloat('nnpolicy', 'regulariser')
        self.regularisation = 'l2'
        if Settings.config.has_option('nnpolicy', 'regularisation'):
            self.regularisation = Settings.config.get('nnpolicy', 'regulariser')
        self.learning_rate = 0.001
        if Settings.config.has_option('nnpolicy', 'learning_rate'):
            self.learning_rate = Settings.config.getfloat('nnpolicy', 'learning_rate')
        self.sarsa_epsilon = 0.05
        if Settings.config.has_option('nnpolicy', 'sarsa_epsilon'):
            self.sarsa_epsilon = Settings.config.getfloat('nnpolicy', 'sarsa_epsilon')
        self.policyfeatures = []
        if Settings.config.has_option('nnpolicy', 'features'):
            logger.info('Features: ' + str(Settings.config.get('nnpolicy', 'features')))
            self.policyfeatures = json.loads(Settings.config.get('nnpolicy', 'features'))
        self.max_k = 5
        if Settings.config.has_option('nnpolicy', 'max_k'):
            self.max_k = Settings.config.getint('nnpolicy', 'max_k')
        self.learning_algorithm = 'sarsa'
        if Settings.config.has_option('nnpolicy', 'learning_algorithm'):
            self.learning_algorithm = Settings.config.get('nnpolicy', 'learning_algorithm')
            logger.info('Learning algorithm: ' + self.learning_algorithm)
        self.learning_mode = 'episodic'
        if Settings.config.has_option('nnpolicy', 'learning_mode'):
            self.learning_mode = Settings.config.get('nnpolicy', 'learning_mode')
        self.minibatch_size = 200
        if Settings.config.has_option('nnpolicy', 'minibatch_size'):
            self.minibatch_size = Settings.config.getint('nnpolicy', 'minibatch_size')
        self.capacity = max(self.minibatch_size, 1000)
        if Settings.config.has_option('nnpolicy', 'capacity'):
            self.capacity = max(self.minibatch_size, Settings.config.getint('policy','capacity'))
        self.shuffle = False
        if Settings.config.has_option('nnpolicy', 'experience_replay'):
            self.shuffle = Settings.config.getboolean('nnpolicy', 'experience_replay')
        if not self.shuffle:
            # If we don't use experience replay, we don't need to maintain
            # sliding window of experiences with maximum capacity.
            # We only need to maintain the data of minibatch_size
            self.capacity = self.minibatch_size

        self.dim_inputs_map = {}
        if 'discourseAct' in self.policyfeatures:
            self.dim_inputs_map['discourseAct'] = len(self.domainUtil.ontology['discourseAct'])
        if 'method' in self.policyfeatures:
            self.dim_inputs_map['method'] = len(self.domainUtil.ontology['method'])
        if 'requested' in self.policyfeatures:
            self.dim_inputs_map['requested'] = len(self.domainUtil.ontology['requestable'])
        if 'kbest' in self.policyfeatures:
            self.dim_inputs_map['kbest'] = 0
            for slot in self.sorted_slots:
                k = min(self.max_k, len(self.domainUtil.ontology['informable'][slot]+['dontcare', '**NONE**']))
                self.dim_inputs_map['kbest'] += k
        if 'full' in self.policyfeatures:
            self.dim_inputs_map['full'] = \
                sum([len(self.domainUtil.ontology['informable'][slot])+1 for slot in self.domainUtil.ontology['informable']])
        if 'lastActionInformNone' in self.policyfeatures:
            self.dim_inputs_map['lastActionInformNone'] = 1
        if 'offerHappened' in self.policyfeatures:
            self.dim_inputs_map['offerHappened'] = 1
        if 'inform_info' in self.policyfeatures:
            self.dim_inputs_map['inform_info'] = 5*5

        self.dim_inputs = sum(self.dim_inputs_map.values())
        logger.info('# dim of NN policy input: '+ str(self.dim_inputs))
        self.policy = Models.fixedOnlineMLPPolicy(
            hidden_structure=self.policy_hidden_structure,
            n_inputs=self.dim_inputs,
            n_outputs=self.numActions,
            regulariser=self.regulariser,
            regularisation=self.regularisation,
            learning_rate=self.learning_rate
            )

        if self.is_training:
            # Training data
            self.data_X = None
            # self.data_y = None
            self.data_a = None
            self.data_r = None
            # self.data_terminal = None
            self.data_aprime = None
            self.data_bprime = None

    def select(self, belief, executable):
        '''
        epsilon-greedy policy
        :return: action index, system action (string), Q-value of chosen action.
        '''
        # Get admissible actions
        admissible = []
        not_admissible = []
        all_action_list = []
        for a in range(self.numActions):
            summary, sys_act = self.to_master_action(a, belief)
            all_action_list.append(sys_act)
            if not sys_act.startswith('null'):
                admissible.append(a)
            else:
                not_admissible.append(a)

        # Compute Qvalue
        flat_belief = self.flatten_belief(belief)
        q_value = self.policy.evaluate([flat_belief])
        q_value = q_value[0]

        # Action selection.
        if self.is_training and Settings.random.rand() < self.sarsa_epsilon:
            # Random action.
            action = Settings.random.choice(admissible)
        else:
            q_value[np.asarray(not_admissible, dtype='int32')] = -np.inf
            # Tie breaking selection.
            action = Settings.random.choice(np.argwhere(q_value == np.amax(q_value)).flatten().tolist())
        return action

    def flatten_belief(self, belief):
        '''
        :return: flattened belief [0.4, 0.2, ...]
        '''
        flat_belief = []
        for feat in self.policyfeatures:
            add_feature = []
            if feat == 'kbest':
                for slot in self.sorted_slots:
                    # print slot, 'belief', belief['beliefs'][slot]
                    temp = [belief['beliefs'][slot][value] for value in self.domainUtil.ontology['informable'][slot]]
                    temp = sorted(temp, key=lambda b: -b)
                    temp = [belief['beliefs'][slot]['**NONE**']] + temp
                    temp = temp[0:self.max_k]
                    # print temp
                    add_feature += temp
            elif feat == 'full':
                for slot in self.sorted_slots:
                    for value in self.domainUtil.ontology['informable'][slot] + ['**NONE**']:
                        add_feature.append(belief['beliefs'][slot][value])
            elif feat == 'method':
                add_feature = [belief['beliefs']['method'][method] for method in self.domainUtil.ontology['method']]
            elif feat == 'discourseAct':
                add_feature = [belief['beliefs']['discourseAct'][discourseAct]
                               for discourseAct in self.domainUtil.ontology['discourseAct']]
            elif feat == 'requested':
                add_feature = [belief['beliefs']['requested'][slot] for slot in self.domainUtil.ontology['requestable']]
            elif feat == 'lastActionInformNone':
                add_feature.append(float(belief['features']['lastActionInformNone']))
            elif feat == 'offerHappened':
                add_feature.append(float(belief['features']['offerHappened']))
            elif feat == 'inform_info':
                add_feature += belief['features']['inform_info']
            else:
                logger.error('Invalid feature name in config: ' + feat)

            flat_belief += add_feature
            if len(add_feature) != self.dim_inputs_map[feat]:
                    logger.error('Dimension mismatch in feature %s: %d expected %d given.'
                                 % (feat, self.dim_inputs_map[feat], len(add_feature)))

        return flat_belief

    '''
    Methods for training policy.
    '''
    def train(self, r):#b, a, r, b_prime=None, a_prime=None):
        '''
        Save training data.
        '''
        if not self.is_training:
            return

        b = self.flatten_belief(self.last_belief)
        a = self.last_act
        b_prime = self.flatten_belief(self.belief)
        a_prime = self.act

        belief = np.asarray([b], dtype='float32')
        action = np.asarray([a], dtype='int32')
        reward = np.asarray([r], dtype='int32')

        # isterminal = (b_prime == None)
        # terminal = np.asarray([isterminal], dtype='bool')

        # Initialise data varaibles
        if self.data_X is None:
            self.data_X = belief
            self.data_a = action
            self.data_r = reward
            # self.data_terminal = terminal
            self.data_bprime = [b_prime]
            self.data_aprime = [a_prime]
        else:
            self.data_X = np.concatenate((self.data_X, belief))
            self.data_a = np.concatenate((self.data_a, action))
            self.data_r = np.concatenate((self.data_r, reward))
            # self.data_terminal = np.concatenate((self.data_terminal, terminal))
            self.data_bprime.append(b_prime)
            self.data_aprime.append(a_prime)

        # If data set is larger than maximal capacity,
        if self.data_X.shape[0] > self.capacity:
            self.data_X = self.data_X[-self.capacity:]
            self.data_a = self.data_a[-self.capacity:]
            self.data_r = self.data_r[-self.capacity:]
            # self.data_terminal = self.data_terminal[-self.capacity:]
            self.data_bprime = self.data_bprime[-self.capacity:]
            self.data_aprime = self.data_aprime[-self.capacity:]

        super(NNPolicy, self).train(r)

    def end_episode(self):
        if not self.is_training:
            return

        # Update Q-value
        self._set_train_data()
        logger.info("Updating Q-value.")
        self.policy.train_model(0, self.policy.train_n.get_value())
       # for j in range(30):
       #     cost = self.policy.train_model(0,len(self.data_X))
       #     result = self.policy.evaluate(self.data_X)
       #
       #     print 'cost =', cost[0], 'Q =',cost[1],'mse =',cost[2]
       #     for i in range(len(self.data_X)):
       #         print result[i,self.data_a[i]], self.data_y[i]

        #pprint.pprint(result)
        #print result[self.data_a]
        #print self.data_y

        # self.sgd = SGD.sgdAlgorithm(self.policy)
        # self.sgd.run(batch_size=len(self.data_X))

    def _set_train_data(self):
        '''
        Transfers collected experiences into theano variables for policy training.
        '''
        index = range(self.data_X.shape[0])
        if self.shuffle and self.learning_algorithm == 'qlearning':
            Settings.random.shuffle(index)
        index = index[-self.minibatch_size:]
        ndata = len(index)

        data_x = self.data_X[index]
        data_r = self.data_r[index]
        data_a = self.data_a[index]
        # data_terminal = self.data_terminal[index]

        next_q = np.zeros(ndata, dtype='float32')
        for i, i_sample in enumerate(index):
            if self.data_bprime[i_sample] is not None: # Nonterminal
                # print i_sample, self.data_bprime[i_sample]
                Q = self.policy.evaluate([self.data_bprime[i_sample]])
                if self.learning_algorithm == 'sarsa':
                    next_q[i] = Q[0][self.data_aprime[i_sample]]
                elif self.learning_algorithm == 'qlearning':
                    next_q[i] = Q[0].max()

        data_y = data_r + self.gamma * next_q
        self.policy.setTrain(data_x, data_y, data_a)

    def save(self, filename):
        param = self.policy.getParameterValues()
        f = open(filename, 'w')
        pickle.dump(param, f)
        f.close()

    def load(self, filename):
        if os.path.isfile(filename):
            logger.info('Loading policy %s.' % filename)
            f = open(filename)
            param = pickle.load(f)
            self.policy.setParameterValues(param)
            f.close()
        elif self.is_training:
            logger.info('Start learning policy: %s.' % filename)
        else:
            logger.error('Policy not found: %s.' % filename)


# class agent_nn(Agent):
#
#     # Parameters.
#     globalActionName = ["INFORM_REQUESTED"
#                         , "INFORM_BYNAME"
#                         #, "INFORM_MORE"
#                         #, "INFORM_REPEAT",
#                         , "REQMORE"
#                         #, "BYE"
#                         , "INFORM_ALTERNATIVES"
#                         #,"RESTART"
#                         ]
#
#     maxAcceptedSlots = 10
#     numGlobalActions = len(globalActionName)
#     printbelief = False
#     disableLowProbAct = False
#     informedVenueSinceNone = []
#     policymode = 'egreedy'
#
#     # Belief
#     k = 5
#
#     # For SARSA
#     gamma = 1.0             # Discount factor.
#     exploringFrozen = False
#     shuffle = False
#
#     # Training data
#     data_X = None
#     data_y = None
#     data_a = None
#     data_r = None
#     data_terminal = None
#
#     config = ConfigParser.ConfigParser()
#     randGenerator = Random()
#
#     # This will be updated in setActions()
#     numSlotActions = 0
#     numActions = 0
#
#     '''
#     RL-Glue agent interface
#     '''
#     def agent_init(self, taskSpecString):
#         TaskSpec = TaskSpecVRLGLUE3.TaskSpecParser(taskSpecString)
#         if TaskSpec.valid:
#             logger.info('TaskSpec parsed: '+taskSpecString)
#         else:
#             logger.info('TaskSpec could not be parsed: '+taskSpecString)
#
#         self.lastAction = Action()
#         self.lastAction.charArray = list('hello()')
#         self.lastObservation = Observation()
#
#     def agent_start(self, observation):
#         self.turn = 0
#         self.lastAction.charArray = list('hello()')
#         self.updateBelief(observation, isstart=True)
#         if (self.printbelief):
#             print ''
#             pprint.pprint(agent_utils._simplifybelief(self.prevstate['beliefs']))
#             if 'features' in self.prevstate:
#                 pprint.pprint(self.prevstate['features'])
#             print ''
#
#         #for a in range(self.numActions):
#         #    summary, sact = self.convertActionToStr(a)
#         #    print a, summary, sact
#
#         # New action
#         if self.policymode == 'egreedy':
#             action, self.Qsa = self.egreedy()
#         else:
#             action, self.Qsa = self.inputact()
#         returnAction = Action()
#         summary, actstr = self.convertActionToStr(action)
#         returnAction.charArray = list(actstr.encode('ascii','replace'))
#         returnAction.intArray = [action]
#
#         self.lastAction = copy.deepcopy(returnAction)
#         self.lastObservation = copy.deepcopy(observation)
#
#         return returnAction
#
#     def agent_step(self, reward, observation):
#         self.turn += 1
#         lastaction = self.lastAction.intArray[0]
#         lastbelief = self.getBelief()
#
#         self.updateBelief(observation)
#         curbelief = self.getBelief()
#
#         if (self.printbelief):
#             print ''
#             pprint.pprint(agent_utils._simplifybelief(self.prevstate['beliefs']))
#             if 'features' in self.prevstate:
#                 pprint.pprint(self.prevstate['features'])
#             print ''
#
#         #for a in range(self.numActions):
#         #    summary, sact = self.convertActionToStr(a)
#         #    print a, summary, sact
#
#         # New action
#         #Q_sa = self.lastQ
#         if self.policymode == 'egreedy':
#             action, self.Qsa = self.egreedy()
#         else:
#             action, self.Qsa = self.inputact()
#         returnAction = Action()
#         summary, actstr = self.convertActionToStr(action)
#         returnAction.charArray = list(actstr.encode('ascii','replace'))
#         returnAction.intArray = [action]
#
#         self.lastAction = copy.deepcopy(returnAction)
#         self.lastObservation = copy.deepcopy(observation)
#
#         # Add training data
#         self._adddata(lastbelief[0], lastaction, reward, curbelief[0], action)
#
#         if self.learning_mode != 'episodic':
#             self.policy.setTrain(self.data_X, self.data_y, self.data_a)
#             self.policy.train_model(0,len(self.data_X))
#             self.data_X = []
#             self.data_a = []
#             self.data_y = []
#
#         return returnAction
#
#     def agent_end(self, reward):
#         lastaction = self.lastAction.intArray[0]
#         lastbelief = self.getBelief()
#
#         # Add training data
#         self._adddata(lastbelief[0], lastaction, reward)
#
#         # Update Q-value
#         self._set_train_data()
#         #logger.info("Updating Q-value")
#         self.policy.train_model(0,self.policy.train_n.get_value())
# #        for j in range(30):
# #            cost = self.policy.train_model(0,len(self.data_X))
# #            result = self.policy.evaluate(self.data_X)
# #
# #            print 'cost =', cost[0], 'Q =',cost[1],'mse =',cost[2]
# #            for i in range(len(self.data_X)):
# #                print result[i,self.data_a[i]], self.data_y[i]
#
#         #pprint.pprint(result)
#         #print result[self.data_a]
#         #print self.data_y
#
#         #self.sgd = SGD.sgdAlgorithm(self.policy)
#         #self.sgd.run(batch_size=len(self.data_X))
#
#     def agent_cleanup(self):
#         pass
#
#     def agent_message(self, inMessage):
#         # 'config config_file'
#         # Action: set policy structure configs
#         if inMessage.startswith("config"):
#             configFile = inMessage.split(" ")
#             self.set_config(configFile[1])
#             return 'Message understood.'
#
#         # 'set-belief-tracker rnn_belief_modelfile'
#         # Action: set belief-tracker tracker
#         if inMessage.startswith('set-belief-tracker'):
#             modelFile = inMessage.split(" ")
#             self.loadTracker(modelFile[1])
#             return 'Message understood'
#
#         # 'print-belief'
#         # Action: print current belief
#         if inMessage.startswith('print-belief'):
#             print self.prevstate
#             return 'Message understood'
#
#         # 'set-print-belief-true'
#         # Action: let the agent print belief at each turn
#         if inMessage.startswith('set-print-belief-true'):
#             self.printbelief = True
#             return 'Message understood'
#
#         # 'set-print-belief-false'
#         if inMessage.startswith('set-print-belief-false'):
#             self.printbelief = False
#             return 'Message understood'
#
#         # 'save-policy filename'
#         if inMessage.startswith('save-policy'):
#             splitString = inMessage.split(' ')
#             self.savePolicy(splitString[1])
#             return 'Message understood'
#
#         # 'load-policy filename'
#         if inMessage.startswith('load-policy'):
#             splitString = inMessage.split(' ')
#             self.loadPolicy(splitString[1])
#             return 'Message understood'
#
#         return 'agent_random does not understand your message'
#
#     def _adddata(self, b, a, r, bprime=None, aprime=None):
#
#         belief = np.asarray([b], dtype='float32')
#         action = np.asarray([a], dtype='int32')
#         reward = np.asarray([r], dtype='int32')
#
#         isterminal = (bprime == None)
#         terminal = np.asarray([isterminal], dtype='bool')
#
#         # Initialise data varaibles
#         if self.data_X == None:
#             self.data_X = belief
#             self.data_a = action
#             self.data_r = reward
#             self.data_terminal = terminal
#             self.data_bprime = [bprime]
#             self.data_aprime = [aprime]
#         else:
#             self.data_X = np.concatenate((self.data_X, belief))
#             self.data_a = np.concatenate((self.data_a, action))
#             self.data_r = np.concatenate((self.data_r, reward))
#             self.data_terminal = np.concatenate((self.data_terminal, terminal))
#             self.data_bprime.append(bprime)
#             self.data_aprime.append(aprime)
#
#         # If data set is larger than maximal capacity,
#         if self.data_X.shape[0] > self.capacity:
#             self.data_X = self.data_X[-self.capacity:]
#             self.data_a = self.data_a[-self.capacity:]
#             self.data_r = self.data_r[-self.capacity:]
#             self.data_terminal = self.data_terminal[-self.capacity:]
#             self.data_bprime = self.data_bprime[-self.capacity:]
#             self.data_aprime = self.data_aprime[-self.capacity:]
#
#     def _set_train_data(self):
#         index = range(self.data_X.shape[0])
# #        print index
#         if self.shuffle and self.learning_algorithm == 'qlearning':
#             self.randGenerator.shuffle(index)
#         index = index[-self.minibatch_size:]
# #        print index
#         ndata = len(index)
#
#         data_X = self.data_X[index]
#         data_r = self.data_r[index]
#         data_a = self.data_a[index]
#         data_terminal = self.data_terminal[index]
#
# #        index_np = np.asarray(index, dtype='int32')
# #        nonterminalindex = index_np[-data_terminal].tolist()
#
# #        print nonterminalindex
#
#         nextQ = np.zeros(ndata,dtype='float32')
#         for i, i_sample in enumerate(index):
#             if self.data_bprime[i_sample] != None: # Nonterminal
#                 Q = self.policy.evaluate([self.data_bprime[i_sample]])
#                 if self.learning_algorithm == 'sarsa':
#                     nextQ[i] = Q[0][self.data_aprime[i_sample]]
#                 elif self.learning_algorithm == 'qlearning':
#                     nextQ[i] = Q[0].max()
#
#         # Q(s',a')
#
# #        Q = self.policy.evaluate(nextbeliefs)
# #        for j, i in enumerate(nonterminalindex):
# #            nextQ[i] = Q[j,nextactions[j]]
#
#         data_y = data_r + self.gamma * nextQ
#         self.policy.setTrain(data_X, data_y, data_a)
#
#     '''
#     Methods for policy
#     '''
#     def savePolicy(self, polfname):
#         param = self.policy.getParameterValues()
#         polf = open(polfname, 'w')
#         pickle.dump(param, polf)
#         polf.close()
#
#     def loadPolicy(self, polfname):
#         polf = open(polfname)
#         param = pickle.load(polf)
#         self.policy.setParameterValues(param)
#         polf.close()
#
#     def inputact(self):
#         '''
#         policy from experts
#         '''
#         for a in range(self.numActions):
#             summary, sact = self.convertActionToStr(a)
#             print a, summary, sact
#
#         action = int(raw_input('sys> '))
#
#         # Compute Qvalue
#         flatbelief = self.getBelief()
#         #flatbelief = np.asarray(self.flatten_belief(), dtype='float32')
#         #print 'belief dimension =', len(flatbelief[0])
#         Q = self.policy.evaluate(flatbelief)
#         Q = Q[0]
#         print Q
#         print 'Q(selected_act) =', Q[action]
#
#         return action, Q[action]
#
#     def egreedy(self):
#         '''
#         epsilon-greedy policy
#         '''
#         # Get admissible actions
#         admissibleActs = []
#         nonAdmissibleActs = []
#         for a in range(self.numActions):
#             summary, sact = self.convertActionToStr(a)
#             if not sact.startswith('null'):
#                 admissibleActs.append(a)
#             else:
#                 nonAdmissibleActs.append(a)
#
#         # Compute Qvalue
#         flatbelief = self.getBelief()
#         #flatbelief = np.asarray(self.flatten_belief(), dtype='float32')
#         #print 'belief dimension =', len(flatbelief[0])
#         Q = self.policy.evaluate(flatbelief)
#         Q = Q[0]
#
#         # Random action
#         if not self.exploringFrozen and self.randGenerator.random() < self.sarsa_epsilon:
#             action = self.randGenerator.choice(admissibleActs)
#         else:
#             Q[np.asarray(nonAdmissibleActs,dtype='int32')] = -np.inf
# #            action = np.argmax(Q)
#             # Tie breaking selection
#             action = self.randGenerator.choice(np.argwhere(Q==np.amax(Q)).flatten().tolist())
#
#         return action, Q[action]
#
#     def getBelief(self):
#         belief = []
#         for feat in self.policyfeatures:
#             if feat == 'kbest':
#                 for slot in self.sorted_slots:
#                     temp = []
#                     for value in self.ontology['informable'][slot]:
#                         temp.append(self.prevstate['beliefs'][slot][value])
#                     temp = sorted(temp, key=lambda b: -b)
#                     belief.append(self.prevstate['beliefs'][slot]['**NONE**'])
#                     belief += temp[0:self.k]
#             elif feat == 'full':
#                 for slot in self.sorted_slots:
#                     for value in self.ontology['informable'][slot] + ['**NONE**']:
#                         belief.append(self.prevstate['beliefs'][slot][value])
#             elif feat == 'method':
#                 for method in self.ontology['method']:
#                     belief.append(self.prevstate['beliefs']['method'][method])
#             elif feat == 'discourseAct':
#                 for discourseAct in self.ontology['discourseAct']:
#                     belief.append(self.prevstate['beliefs']['discourseAct'][discourseAct])
#             elif feat == 'requested':
#                 for slot in self.ontology['requestable']:
#                     belief.append(self.prevstate['beliefs']['requested'][slot])
#             elif feat == 'lastActionInformNone':
#                 belief.append(float(self.prevstate['features']['lastActionInformNone']))
#             elif feat == 'offerHappened':
#                 belief.append(float(self.prevstate['features']['offerHappened']))
#             elif feat == 'inform_info':
#                 belief += self.prevstate['features']['inform_info']
#             else:
#                 logger.warning('Invalid feature name in config: ' + feat)
#
#
#         return [belief]
#
#     '''
#     Methods for belief tracking
#     '''
#     def updateBelief(self, obs, isstart=False):
#         curturn = self.convertHypToTurn(obs)
#         #print curturn
#         if (isstart):
#             self.prevstate = self.tracker.trackSingleTurn(curturn)
#         else:
#             self.prevstate = self.tracker.trackSingleTurn(curturn, self.prevstate)
#
#         self._appendbelief(isstart)
#
#     def _appendbelief(self, isstart):
#         '''
#         Add context features into self.prevstate
#         '''
#         self._updateMactFeat(isstart)
#
#     def _updateMactFeat(self, isstart):
#         '''
#         Add features from system action into self.prevstate
#         '''
#         lastsact = dact.ParseAct(''.join(self.lastAction.charArray), False)
#         #print ''.join(self.lastAction.charArray)
#
#         features = {}
#         # lastInformedVenue
#         features['lastInformedVenue'] = agent_utils._getCurrentInformedVenue(lastsact)
#
#         # informedVenueSinceNone
#         if isstart:
#             self.informedVenueSinceNone = []
#
#         if agent_utils._hasType(lastsact, 'canthelp'):
#             self.informedVenueSinceNone = []
#         if agent_utils._hasTypeSlot(lastsact, 'offer', 'name'):
#             venue = agent_utils._getTypeSlot(lastsact, 'offer', 'name')
#             self.informedVenueSinceNone.append(venue)
#         features['informedVenueSinceNone'] = self.informedVenueSinceNone
#
#         # lastActionInformNone
#         if agent_utils._hasType(lastsact, 'canthelp'):
#             features['lastActionInformNone'] = True
#         else:
#             features['lastActionInformNone'] = False
#
#         # offerHappened
#         if agent_utils._hasTypeSlot(lastsact, 'offer', 'name'):
#             features['offerHappened'] = True
#         else:
#             features['offerHappened'] = False
#
#         # inform_info
#         features['inform_info'] = []
#         for numAccepted in range(1,6):
#              features['inform_info'] += self.townInfoActionSpecificInformSummary(numAccepted)
#
#         self.prevstate['features'] = features
#
#     def convertHypToTurn(self, obs):
#         hypstr = ''.join(obs.charArray)
#         hyplist = hypstr.split('\t')
#
#         curturn = {"turn-index": self.turn}
#         slastact = []
#         if (self.turn > 0):
#             slastact = dact.ParseAct(''.join(self.lastAction.charArray), False)
#             slastact = agent_utils._transformAct(slastact, {}, self.ontology, False)
#         curturn['output'] = {'dialog-acts': slastact}
#
#         accumulated = defaultdict(float)
#         for i in range(len(hyplist)):
#             hyp = dact.ParseAct(hyplist[i])
#             hyp = agent_utils._transformAct(hyp, {}, self.ontology)
#             hyp = dact.inferSlotsForAct(hyp)
#
#             prob = obs.doubleArray[i]
#             prob = min(1.0, prob)
#             if (prob < 0): prob = exp(prob)
#             accumulated = agent_utils._addprob(accumulated, hyp, prob)
#
#         sluhyps = agent_utils._normaliseandsort(accumulated)
#         curturn["input"] = {"live":{"asr-hyps":[], "slu-hyps":sluhyps}}
#         return curturn
#
#     '''
#     Methods for setup
#     '''
#     def set_config(self, configfile):
#         logger.info("Loading config file: "+configfile)
#         try:
#             self.config.read(configfile)
#         except Exception as inst:
#             logger.info("Failed to parse config file: "+configfile)
#             raise
#
#         ontology_fname = self.config.get("classifier", "ontology")
#         logger.info('Loading ontology: '+ontology_fname)
#         self.setOntology(json.load(open(ontology_fname)))
#         db_fname = self.config.get("classifier", "database")
#         logger.info('Loading database: '+db_fname)
#         self.db = agent_utils.loaddb(db_fname)
#         logger.info('Configuring possible system action.')
#         self.setActions()
#         logger.info('Loading belief tracker.')
#         self.loadTracker()
#
#         logger.info('Initialise fixedMLP for policy.')
#         self.policy_hidden_structure = []
#         if self.config.has_option("policy", "hidden_structure"):
#             self.policy_hidden_structure = json.loads(self.config.get("policy", "hidden_structure"))
#         self.regulariser = 0.0
#         if self.config.has_option('policy','regulariser'):
#             self.regulariser = float(self.config.get('policy','regulariser'))
#         self.regularisation = 'l2'
#         if self.config.has_option('policy','regularisation'):
#             self.regularisation = self.config.get('policy','regulariser')
#         self.learning_rate = 0.001
#         if self.config.has_option('policy','learning_rate'):
#             self.learning_rate = float(self.config.get('policy','learning_rate'))
#         self.sarsa_epsilon = 0.05
#         if self.config.has_option('policy','sarsa_epsilon'):
#             self.sarsa_epsilon = float(self.config.get('policy','sarsa_epsilon'))
#         self.policyfeatures = []
#         if self.config.has_option('policy','features'):
#             logger.info('Features: ' + str(self.config.get('policy','features')))
#             self.policyfeatures = json.loads(self.config.get('policy','features'))
#         self.learning_algorithm = 'sarsa'
#         if self.config.has_option('policy','learning_algorithm'):
#             self.learning_algorithm = self.config.get('policy','learning_algorithm')
#             logger.info('Learning algorithm: ' + self.learning_algorithm)
#         self.learning_mode = 'episodic'
#         if self.config.has_option('policy','learning_mode'):
#             self.learning_mode = self.config.get('policy','learning_mode')
#         self.minibatch_size = 200
#         if self.config.has_option('policy','minibatch_size'):
#             self.minibatch_size = int(self.config.get('policy','minibatch_size'))
#         self.capacity = max(self.minibatch_size, 1000)
#         if self.config.has_option('policy','capacity'):
#             self.capacity = max(self.minibatch_size, int(self.config.get('policy','capacity')))
#         if self.shuffle == False:
#             # If we don't use experience replay, we don't need to maintain
#             # sliding window of experiences with maximum capacity.
#             # We only need to maintain the data of minibatch_size
#             self.capacity = self.minibatch_size
#
#         dim_inputs = 0
#         if 'discourseAct' in self.policyfeatures:
#             dim_inputs += len(self.ontology['discourseAct'])
#         if 'method' in self.policyfeatures:
#             dim_inputs += len(self.ontology['method'])
#         if 'requested' in self.policyfeatures:
#             dim_inputs += len(self.ontology['requestable'])
#         if 'kbest' in self.policyfeatures:
#             for slot in self.sorted_slots:
#                 k = min(self.k, len(self.ontology['informable'][slot]))
#                 dim_inputs += k + 1
#         if 'full' in self.policyfeatures:
#             dim_inputs += sum([len(self.ontology['informable'][slot])+1 for slot in self.ontology['informable']])
#         if 'lastActionInformNone' in self.policyfeatures:
#             dim_inputs += 1
#         if 'offerHappened' in self.policyfeatures:
#             dim_inputs += 1
#         if 'inform_info' in self.policyfeatures:
#             dim_inputs += 5*5
#
#         logger.info('# dim of NN policy input: '+ str(dim_inputs))
#         self.policy = Models.fixedOnlineMLPPolicy(
#             hidden_structure = self.policy_hidden_structure,
#             n_inputs = dim_inputs,
#             n_outputs = self.numActions,
#             regulariser = self.regulariser,
#             regularisation = self.regularisation,
#             learning_rate = self.learning_rate
#             )
#
#         return
#
#     def setOntology(self, ont):
#         '''
#         Sets the ontology to the specified json
#         '''
#         self.ontology = ont
#
#         self.sorted_values = {}
#
#         for slot in self.ontology["informable"] :
#             self.sorted_values[slot] = self.ontology["informable"][slot] + ["dontcare"]
#             self.sorted_values[slot].sort()
#
#         self.sorted_slots = list(self.ontology["informable"])
#         self.sorted_slots.sort()
#
#         # set sorted_methods:
#         self.sorted_methods = self.ontology["method"]
#         self.sorted_methods.sort()
#
#         # sort requestable
#         self.requestable = self.ontology["requestable"]
#         self.requestable = agent_utils.order_using(self.requestable, self.sorted_slots)
#
#         # set discourseAct:
#         if "discourseAct" in self.ontology :
#             self.sorted_discourseAct = self.ontology["discourseAct"]
#             self.sorted_discourseAct.sort()
#
#     def loadTracker(self):
#         self.tracker = Tracker.createTracker(self.config, no_train=True)
#         self.tracker.initializeFromConfig()
#
#     def setActions(self):
#         '''
#         Sets the number of possible system actions (self.numActions and self.numSlotActions).
#         See SlotBasedActionList in the vocaliq system
#         '''
#
#         maxAccepted = 0
#         self.numSlotActions = 0
#         self.slotActToSlotname = []
#
#         for slot in self.sorted_slots:
#             if slot != 'name':
#                 maxAccepted = maxAccepted + 1
#                 self.numSlotActions = self.numSlotActions + 3
#                 self.slotActToSlotname.append(slot)
#                 self.slotActToSlotname.append(slot)
#                 self.slotActToSlotname.append(slot)
#
#         if (self.maxAcceptedSlots < maxAccepted):
#             maxAccepted = self.maxAcceptedSlots
#
#         self.numActions = self.numSlotActions + self.numGlobalActions + maxAccepted
#         logger.info("numActions = "+str(self.numActions))
#         return
#
#     def convertActionToStr(self, action):
#         summary, sact = self._slotBasedActionMapping(action, self.prevstate)
#         return summary, sact
#
#     def _slotBasedActionMapping(self, action, belief):
#         '''
#         Maps the given action index to summary action.
#         '''
#         #feature = belief["features"]
#         #lastInformedVenue = feature["lastInformedVenue"]
#
#         if (action < self.numSlotActions):
#             subaction = action % 3
#             return self._computeSlotLevelAction(self.slotActToSlotname[action], subaction)
#         if (action < self.numSlotActions + self.numGlobalActions):
#             return self._computeGlobalAction(action - self.numSlotActions)
#         if (action < self.numSlotActions + self.numGlobalActions + self.maxAcceptedSlots):
#             return self._computeInformAction(action - self.numSlotActions - self.numGlobalActions + 1)
#         return 'invalid', 'null()'
#
#     def _computeInformAction(self, numAccepted):
#         summaryActionName = 'inform_' + str(numAccepted)
#         return summaryActionName, self.getInformAction(numAccepted)
#
#     def getInformAction(self, numAccepted):
#         acceptanceList = self._getTopBeliefs()
#         if numAccepted > len(acceptanceList):
#             return 'null()'
#
#         return self.getInformExactEntity(acceptanceList, numAccepted)
#
#     def getInformExactEntity(self, acceptanceList, numAccepted):
#
#         acceptedValues = {}
#         for i, slot in enumerate(acceptanceList):
#             if i >= numAccepted:
#                 break
#             (topvalue, topbelief) = acceptanceList[slot]
#             if topvalue != 'dontcare':
#                 acceptedValues[slot] = topvalue
#
#         result = self.getMatchingEntities(acceptedValues)
#         if len(result) == 0:
#             return self.getInformNoneVenue(acceptedValues)
#         else:
#             ent = result[0]
#             return self.getInformAcceptedSlotsAboutEntity(acceptanceList, ent, numAccepted)
#
#     def _computeGlobalAction(self, globalact):
#         if (globalact < self.numGlobalActions):
#             summaryActionName = 'global_' + self.globalActionName[globalact]
#         else:
#             #summaryActionName = 'global_' + str(globalact)
#             logger.info('WARNING: invalid global action number '+globalact)
#             return 'invalid','null()'
#
#         #lastven = self.prevstate['featureslastInformedVenue']
#         output = self._getGlobalAction(globalact)
#         return summaryActionName, output
#
#     def _getGlobalAction(self, globalact):
#         # First get the name fro the name goal.
#         topvalue, topbelief = self._getTopBelief(self.prevstate['beliefs']['name'])
#         toptwo = self._getTopTwoBeliefsExcludingNone('name')
#         if (topvalue == '**NONE**' or topvalue == 'dontcare' or topbelief < 0.8):
#             topnamevalue = ''
#         else:
#             topnamevalue = toptwo[0][0]
#
#         lastInformedVenue = self.prevstate['features']['lastInformedVenue']
#         informedVenueSinceNone = self.prevstate['features']['informedVenueSinceNone']
#         acceptanceList = self._getTopBeliefs()
#         acceptanceList80 = self._getTopBeliefs(0.8)
#         requestedSlots = self._getRequestedSlots()
#
#         if (topnamevalue == '' and lastInformedVenue != ''):
#             topnamevalue = lastInformedVenue
#
#         if (self.globalActionName[globalact] == 'INFORM_REQUESTED'):
#             if (topnamevalue != ''):
#                 return self._getInformRequestedSlots(acceptanceList80, requestedSlots, topnamevalue)
#             else:
#                 return self._getInformRequestedSlots(acceptanceList80, requestedSlots, 'none')
#         elif (self.globalActionName[globalact] == 'INFORM_ALTERNATIVES'):
#             if (lastInformedVenue == ''):
#                 return 'null()'
#             else:
#                 return self._getInformAlternativeEntities(acceptanceList, acceptanceList80, self.prevstate['features']['informedVenueSinceNone'])
#         elif (self.globalActionName[globalact] == 'INFORM_MORE'):
#             if (len(informedVenueSinceNone) > 0 and topnamevalue != ''):
#                 return self._getInformMoreEntity(topnamevalue)
#             else:
#                 return self._getInformMoreEntity('none')
#         elif (self.globalActionName[globalact] == 'INFORM_BYNAME'):
#             return self._getInformAlternativeEntities(acceptanceList, acceptanceList80, [])
#         elif (self.globalActionName[globalact] == 'INFORM_REPEAT'):
#             return 'null()'
#         elif (self.globalActionName[globalact] == 'REQMORE'):
#             if (lastInformedVenue != ''):
#                 return 'reqmore()'
#             else:
#                 return 'null()'
#         elif (self.globalActionName[globalact] == 'BYE'):
#             return 'bye()'
#         elif (self.globalActionName[globalact] == 'RESTART'):
#             return 'null()'
#         else:
#             logger.warning('Invalid global action number '+globalact)
#             return 'null()'
#
#     def _getInformMoreEntity(self, name):
#         '''
#         Finds the last informed entity and it informs about the non-accepted slots.
#         @param name the last informed entity
#         '''
#         result = self.getMatchingEntities({'name':name})
#         if name != 'none' and len(result) > 0:
#             ent = result[0]
#             return self.getInformCommentSlotAboutEntity(ent)
#         else:
#             return 'null()'
#
#     def getMatchingEntities(self, constraints):
#         result = []
#         for id in self.db:
#             entity = self.db[id]
#             match = True
#             for slot in constraints:
#                 value = constraints[slot]
#                 if not entity.has_key(slot):
#                     match = False
#                     break
#
#                 if entity[slot] != value:
#                     match = False
#                     break
#
#             if match:
#                 result.append(self.db[id])
#         #pprint.pprint(result)
#         return result
#
#     def _getInformAlternativeEntities(self, acceptanceList, acceptanceList80, prohibitedList):
#         '''
#         Returns the dialogue act representing either
#         1) there is not matching venue: inform(name=none, slot=value, ...)
#         2) it offers a venue which is not on the prohibited list
#         3) if all matching venues are on the prohibited list then it says
#            there is no venue except x,y,z,... with such features:
#            inform(name=none, name!=x, name!=y, name!=z, ..., slot=value, ...)
#         '''
#         acceptedValues = {}
#         numFeats = len(acceptanceList80)
#         for slot in acceptanceList80:
#             (topvalue, topbelief) = acceptanceList80[slot]
#             if (topvalue != 'dontcare'):
#                 acceptedValues[slot] = topvalue
#
#         if len(acceptedValues) == 0:
#             return 'null()'
#
#         result = self.getMatchingEntities(acceptedValues)
#         if len(result) == 0:
#             return self.getInformNoneVenue(acceptedValues)
#         else:
#             for ent in result:
#                 name = ent['name']
#                 if not name in prohibitedList:
#                     return self.getInformAcceptedSlotsAboutEntity(acceptanceList, ent, numFeats)
#
#             return self.getInformNoMoreVenues(acceptanceList, result, numFeats)
#
#         return 'null()'
#
#     def getInformNoMoreVenues(self, acceptanceList, entities, numFeats):
#         ans = 'inform(name=none,'
#
#         for ent in entities:
#             ans += 'name!="' + ent['name'] + '",'
#
#         feats = {}
#         for count, slot in enumerate(acceptanceList):
#             if count >= numFeats:
#                 break
#
#             if slot == 'name':
#                 continue
#
#             (value, belief) = acceptanceList[slot]
#             if value == 'dontcare':
#                 continue
#
#             feats[slot] = value
#
#         ans += agent_utils.convertFeatsToStr(feats) + ')'
#         return ans
#
#     def getInformAcceptedSlotsAboutEntity(self, acceptanceList, ent, numFeats):
#         '''
#         need to be cleaned
#         '''
#         ans = 'inform('
#         feats = {'name': ent['name']}
#
#         for i, slot in enumerate(acceptanceList):
#             if i >= numFeats:
#                 break
#             if slot == 'name':
#                 continue
#
#             (value, belief) = acceptanceList[slot]
#             if value == 'dontcare' and slot in ent:
#                 feats[slot] = ent[slot]
#             else:
#                 if not slot in ent:
#                     feats[slot] = 'none'
#                 else:
#                     feats[slot] = value
#         ans += agent_utils.convertFeatsToStr(feats) + ')'
#         return ans
#
#     def getInformNoneVenue(self, acceptedValues):
#         feats = self.findMinimalAcceptedSetForNoEntities(acceptedValues)
#         return 'inform(name=none, '+agent_utils.convertFeatsToStr(feats)+')'
#
#     def findMinimalAcceptedSetForNoEntities(self, acceptedValues):
#         keeping = copy.deepcopy(acceptedValues)
#         if len(acceptedValues) > 1:
#             result = self.getMatchingEntities(acceptedValues)
#             if len(result) == 0:
#                 for slot in acceptedValues:
#                     if slot != 'type':
#                         del keeping[slot]
#                         result2 = self.getMatchingEntities(keeping)
#                         if len(result2) > 0:
#                             keeping[slot] = acceptedValues[slot]
#
#         return keeping
#
#     def _getInformRequestedSlots(self, acceptanceList80, requestedSlots, name):
#         result = self.getMatchingEntities({'name':name})
#
#         acceptedValues = {}
#         for slot in acceptanceList80:
#             (topvalue, topbelief) = acceptanceList80[slot]
#             if (topvalue != 'dontcare'):
#                 acceptedValues[slot] = topvalue
#
#         if len(result) > 0 and name != 'none':
#             # We found exactly one or more matching entities. Use the first one
#             ent = result[0]
#             return self._getInformRequestedSlotsForEntity(acceptedValues, requestedSlots, ent)
#         else:
#             # We have not informed about an entity yet, or there are too many entities.
#             return 'null()'
#
#     def _getInformRequestedSlotsForEntity(self, acceptedValues, requestedSlots, ent):
#         '''
#         @param acceptedValues sufficiently confident slot values
#         @param requestedSlots list of requested slots
#         should be improved: acceptedValues may not be needed
#         '''
#         #print 'requested slots: ', requestedSlots
#
#         ans = 'inform('
#
#         slotvaluepair = ['name="'+ent['name']+'"']
#         if len(requestedSlots) == 0:
#             slotvaluepair = ['type="'+ent['type']+'"']
#
#         # Should inform about requested slots.
#         for i in range(len(requestedSlots)):
#             slot = requestedSlots[i]
#
#             if i > 5:
#                 break
#
#             if slot == 'name' or slot == 'location':
#                 break
#
#             acceptedValue = ''
#             requestedSlotFound = False
#
#             if slot in acceptedValues:
#                 acceptedValue = acceptedValues[slot]
#
#             if slot in ent:
#                 slotvaluepair.append(slot+'="'+ent[slot]+'"')
# #            if slot in ent and acceptedValue == ent[slot]:
# #                slotvaluepair.append(slot+'="'+acceptedValue+'"')
# #            elif slot in ent and not slot in acceptedValues:
# #                '''
# #                added only if its value is not accepted
# #                '''
# #                slotvaluepair.append(slot+'="'+ent[slot]+'"')
#             else:
#                 slotvaluepair.append(slot+'=none')
#
#         ans += ','.join(slotvaluepair) + ')'
#         return ans
#
#
#
#     def _getRequestedSlots(self):
#         # Iterate over only goal slots
#         ans = []
#         for slot in self.prevstate['beliefs']['requested']:
#             #if slot in self.ontology['informable'] or slot == 'name':
#             #    continue
#             requestprob = self.prevstate['beliefs']['requested'][slot]
#             if (requestprob > 0.5):
#                 ans.append(slot)
#         return ans
#
#     def _computeSlotLevelAction(self, slot, action):
#
#         # number of possible slot values excluding N/A
#         numvalues = len(self.ontology["informable"][slot])
#         minBeliefForConfirm = 1.0 / (float(numvalues)-0.1)
#
#         # Get top two beliefs
#         toptwo = self._getTopTwoBeliefsExcludingNone(slot)
#         topvalue = toptwo[0][0]
#         topbelief = toptwo[0][1]
#
#
#         if (action == 0): # Request.
#             summaryActionName = "request_" + slot
#             output = "request("
#
#             # Add implicit confirmation
#             #needGrounding = self._getNodesNeedingImplicitConfirmation(slot)
#             needGrounding = self._getTopBeliefs(0.8)
#             if (needGrounding.has_key(slot)):
#                 del needGrounding[slot]
#             #acceptanceList = self._getNodeAcceptanceListacceptanceList80 = self._getTopBeliefs(0.8)(goalBelief)
#             acceptanceList = self._getTopBeliefs(threshold='auto')
#
#             if (len(acceptanceList) > 0 and len(needGrounding) > 0):
#                 foundThis = False
#                 if (acceptanceList.has_key(slot)):
#                     (_, prob) = acceptanceList[slot]
#                     if (prob > 0.8):
#                         foundThis = True
#
#                 # If there is no accepted value, add implicit confirmation
#                 if (foundThis == False):
#                     output = "confreq("
#                     slotvaluepair = []
#                     for slotname in needGrounding:
#                         if (len(slotvaluepair) < 3):
#                             (value, prob) = needGrounding[slotname]
#                             slotvaluepair.append(slotname + '="' + value + '"')
#                     output = output + ','.join(slotvaluepair) + ','
#
#             output = output + slot + ')'
#
#         elif (action == 1): # Confirm.
#             summaryActionName = "confirm_" + slot
#             if (self.disableLowProbAct == False or topbelief > minBeliefForConfirm):
#                 output = 'confirm('+slot+'="'+topvalue+'")'
#             else:
#                 output = 'null()'
#
#         elif (action == 2): # Select.
#             summaryActionName = "select_" + slot
#             if (self.disableLowProbAct == False or (topbelief > minBeliefForConfirm and len(toptwo) == 2)):
#                 output = 'select('+slot+'="'+topvalue+'",'
#                 output += slot+'="'+toptwo[1][0]+'")'
#             else:
#                 output = 'null()'
#
#         else:
#             summaryActionName = "invalid_" + slot
#             output = 'null()'
#
#         return summaryActionName, output
#
#
#
#     def _getNodeAcceptanceList(self):
#         '''
#         Get the accepted nodes
#         might be deleted
#         '''
#         ans = {}
#         name = ''
#         for slot in self.sorted_slots:
#             #topthree = self._getTopThreeBeliefs(slot)
#             topBelief, topVal = self._getTopBelief(self.prevstate['beliefs'][slot])
#             numvalues = len(self.ontology['informable'][slot])
#             minBeliefForAccept = 1. / (float(numvalues) - 0.1)
#             if (topVal != '**NONE**' and topBelief > minBeliefForAccept):
#                 if slot == 'name':
#                     name = topVal
#                 else:
#                     ans[slot] = (topVal, topBelief)
#         return ans, name
#
#     def _getTopBeliefs(self, threshold='auto'):
#         '''
#         Get slot values which have the belief larger than threshold
#         @return {slot: (topvalue, topbelief), ...}
#         '''
#         ans = {}
#         for slot in self.sorted_slots:
#             if slot == 'name':
#                 continue
#
#             if (threshold == 'auto'):
#                 numvalues = len(self.ontology['informable'][slot])
#                 thres = 1. / (float(numvalues) - 0.1)
#             else:
#                 thres = threshold
#
#             topvalue, topbelief = self._getTopBelief(self.prevstate['beliefs'][slot])
#
#
#             if (topvalue != '**NONE**' and topbelief > thres):
#                 ans[slot] = (topvalue, topbelief)
#
#         return ans
#
#     def _getNodesNeedingImplicitConfirmation(self, slotToExclude):
#         '''
#         may be deleted
#         Get slots which should be implicitly confirmed
#         @param slotToExclude: This slot will be excluded in implicit confirmation
#         @return [(slot, topvalue),(slot, topvalue),...]
#         '''
#         ans = []
#         for slot in self.sorted_slots:
#             if slot == 'name' or slot == slotToExclude:
#                 continue
#
#             topvalue, topbelief = self._getTopBelief(self.prevstate['beliefs'][slot])
#             if (topvalue != '**NONE**' and topbelief > 0.8):
#                 ans.append((slot, topvalue))
#
#         return ans
#
#     def _getTopTwoBeliefsExcludingNone(self, slot):
#         '''
#         may be deleted
#         '''
#         slotbelief = copy.deepcopy(self.prevstate['beliefs'][slot])
#         ans = []
#         while (len(ans) < 2 or len(slotbelief) > 0):
#             topvalue, topbelief = self._getTopBelief(slotbelief)
#             if (topvalue != '**NONE**'):
#                 ans.append((topvalue, topbelief))
#             del slotbelief[topvalue]
#
#         return ans
#
#     def _getTopThreeBeliefs(self, slot):
#         '''
#         may be deleted
#         '''
#         slotbelief = copy.deepcopy(self.prevstate['beliefs'][slot])
#         firstvalue, firstbelief = self._getTopBelief(slotbelief)
#         del slotbelief[firstvalue]
#         secondvalue, secondbelief = self._getTopBelief(slotbelief)
#         del slotbelief[firstvalue]
#         thirdvalue, thirdbelief = self._getTopBelief(slotbelief)
#         return [(firstvalue, firstbelief), (secondvalue, secondbelief), (thirdvalue, thirdbelief)]
#
#     def _getTopBelief(self, slotbelief):
#         '''
#         Return slot value with the largest belief
#         '''
#         topvalue = max(slotbelief.iterkeys(), key=(lambda key: slotbelief[key]))
#         topbelief = slotbelief[topvalue]
#         return topvalue, topbelief
#
#     def townInfoActionSpecificInformSummary(self, numAccepted):
#         '''
#         TownInfoActionSpecificInformSummary
#         count: # of matching entities
#         discriminatable: matching entities can be further discriminated
#         @return summaryArray [(count == 0), (count == 1), (count==2), (count==3), discriminatable]
#         '''
#         acceptanceList = self._getTopBeliefs()
#         count = self._countEntitiesForAcceptanceListPart(acceptanceList, numAccepted)
#         if count > 1 and count <= 4:
#             count = 2
#         elif count > 4:
#             count = 3
#
#         summaryArray = self._setSummaryStateDiscreteFeature(4, count)
#         discriminatable = self._acceptanceListCanBeDiscriminated(acceptanceList, numAccepted)
#         summaryArray += [int(discriminatable)]
#         return summaryArray
#
#     def _countEntitiesForAcceptanceListPart(self, acceptanceList, numAccepted):
#         '''
#         Returns the number of entities matching the first self.maxAcceptedSlots (default=10)
#         values in the acceptance list. Includes values with dontcare in the count
#         @param acceptanceList {slot: (topvalue, topbelief), ...}
#         '''
#         acceptedValues = {}
#         countVals = 0
#         countEnts = 40
#
#         for slot in acceptanceList:
#             (topvalue, _) = acceptanceList[slot]
#             if topvalue != 'dontcare':
#                 acceptedValues[slot] = topvalue
#             countVals += 1
#             if countVals >= numAccepted:
#                 break
#
#         if len(acceptedValues) > 0:
#             result = self.getMatchingEntities(acceptedValues)
#             countEnts = len(result)
#
#         return countEnts
#
#     def _acceptanceListCanBeDiscriminated(self, acceptanceList, numAccepted):
#         '''
#         Checks if the given acceptance list with the given number of values accepted
#         returns a list of values which can be discriminated between -
#         i.e. there is a question which we could ask which would give differences between
#         the values.
#         Note that only slots from the full acceptanceList (i.e. not just below
#         maxAcceptedSlots are used for discrimination to exclude things like phone, addr, etc)
#         '''
#         acceptedValues = {}
#         discriminatingSlots = set()
#         i=0
#         for slot in acceptanceList:
#             if i < numAccepted:
#                 (topvalue, _) = acceptanceList[slot]
#                 if topvalue != 'dontcare':
#                     acceptedValues[slot] = topvalue
#             else:
#                 discriminatingSlots.add(slot)
#             i += 1
#
#         for slot in self.sorted_slots:
#             if slot != 'name':
#                 discriminatingSlots.add(slot)
#
#         result = self.getMatchingEntities(acceptedValues)
#
#         otherFeats = {}
#         for ent in result:
#             for slot in ent:
#                 val = ent[slot]
#
#                 # this slot was one of the constraints or dontcare
#                 if not slot in acceptedValues and slot in discriminatingSlots:
#                     if not slot in otherFeats or otherFeats[slot] == val:
#                         otherFeats[slot] = val
#                     else:
#                         # This slot will allow discrimination and isn't in the constraints
#                         return True
#
#         return False
#
#
#     def _setSummaryStateDiscreteFeature(self, size, feature):
#         '''
#         Sets a part of summary state with a discrete value
#         '''
#         vect = []
#         for j in range(size):
#             if j == feature:
#                 vect.append(1)
#             else:
#                 vect.append(0)
#         return vect
