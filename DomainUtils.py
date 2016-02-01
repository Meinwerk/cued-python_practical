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
DomainUtils.py - perform ontology queries
===========================================

Authors: Dongho Kim, David Vandyke  (Copyright CUED Dialogue Systems Group 2015)

**Relevant Config variables** [Default values]::

    [DEFAULT]
    root = ''    - which is the path to root directory of python system. Use when running grid jobs.
 
.. seealso:: CUED Imports/Dependencies: 

    import :class:`Settings` |.|
    import :class:`ContextLogger`

************************

'''
__author__="donghokim, davidvandyke"
import copy, math, json
import numpy as np

import Settings
import DataBase
import ContextLogger
logger = ContextLogger.getLogger('')

root='' # for running on grid etc where path may not be local. Set via config under [DEFAULTS]
ont_db_pairs = {\
            'TSB6':{'ontology':root+'ontology/TSB6-rules.json','database':root+'ontology/TSB6-dbase.txt'},
            'TSB11':{'ontology':root+'ontology/TSB11-rules.json','database':root+'ontology/TSB11-dbase.txt'},
            'TSBtele':{'ontology':root+'ontology/TSBtele-rules.json','database':root+'ontology/TSBtele-dbase.txt'},
            'TSBextHD':{'ontology':root+'ontology/TSBextHD-rules.json','database':root+'ontology/TSBextHD-dbase.txt'},
            'TSBplayer':{'ontology':root+'ontology/TSBplayer-rules.json','database':root+'ontology/TSBplayer-dbase.txt'},
            'SFR':{'ontology':root+'ontology/SFR-rules.json','database':root+'ontology/SFR-dbase.txt'},
            'SFH':{'ontology':root+'ontology/SFH-rules.json','database':root+'ontology/SFH-dbase.txt'},
            'TT':{'ontology':root+'ontology/TT-rules.json', 'database':root+'ontology/TT-dbase.txt'},
            'CamShop':{'ontology':root+'ontology/CamShop-rules.json','database':root+'ontology/CamShop-dbase.txt'},
            'CamAttrac':{'ontology':root+'ontology/CamAttrac-rules.json','database':root+'ontology/CamAttrac-dbase.txt'},
            'CamTrans':{'ontology':root+'ontology/CamTrans-rules.json','database':root+'ontology/CamTrans-dbase.txt'},
            'CamHotels':{'ontology':root+'ontology/CamHotels-rules.json','database':root+'ontology/CamHotels-dbase.txt'},
           }
available_domains = ont_db_pairs.keys()

# For Multi-domain dialog - determining which of the allowed (config specified) domains can be paired together:
# Dont want to have a combinatorial explosion here - so make it linear and set allowed partners for each domain:
# TODO - just specifying GROUPS may be a simpler approach here ... 
#-------- Hand Coded codomain rules:
ALLOWED_CODOMAIN_RULES = dict.fromkeys(ont_db_pairs.keys())
ALLOWED_CODOMAIN_RULES["TSB6"] = ["TSBtele","TSBextHD","TSBplayer"]
ALLOWED_CODOMAIN_RULES["TSB11"] = ["TSBtele","TSBextHD","TSBplayer"]
ALLOWED_CODOMAIN_RULES["TSBtele"] = [["TSB6","TSBextHD","TSBplayer"], ["TSB11","TSBextHD","TSBplayer"]]
ALLOWED_CODOMAIN_RULES["TSBextHD"] = [["TSBtele","TSB11","TSBplayer"], ["TSB6","TSBtele","TSBplayer"]]
ALLOWED_CODOMAIN_RULES["TSBplayer"] = [["TSBtele","TSBextHD","TSB6"],["TSBtele","TSBextHD","TSB11"]]
ALLOWED_CODOMAIN_RULES["SFR"] = ["SFH"]
ALLOWED_CODOMAIN_RULES["SFH"] = ["SFR"]
ALLOWED_CODOMAIN_RULES["TT"] = ["CamHotels","CamShop", "CamAttrac","CamTrans"] 
ALLOWED_CODOMAIN_RULES["CamTrans"] = ["CamHotels","CamShop", "CamAttrac","TT"] 
ALLOWED_CODOMAIN_RULES["CamAttrac"] = ["CamHotels","CamShop", "TT","CamTrans"] 
ALLOWED_CODOMAIN_RULES["CamShop"] = ["CamHotels","TT", "CamAttrac","CamTrans"] 
ALLOWED_CODOMAIN_RULES["CamHotels"] = ["TT","CamShop", "CamAttrac","CamTrans"] 
#-----------------------------------------


#TODO add these for each domain  - or write something better like a tool to determine this from ontology
# Note that ALL ONTOLOGIES should be representing binary values as 0,1  (Not true,false for example)
# These are used to check whether we can process a yes/no response as e.g. an implicit inform(true)
BINARY_SLOTS = dict.fromkeys(ont_db_pairs.keys())
BINARY_SLOTS['CamHotels'] = ['hasparking']
BINARY_SLOTS['SFH'] = ['dogsallowed','hasinternet','acceptscreditcards']
BINARY_SLOTS['SFR'] = ['allowedforkids']
BINARY_SLOTS['TSB6'] = ['isforbusinesscomputing']
BINARY_SLOTS['TSB11'] = ['isforbusinesscomputing']
BINARY_SLOTS['TSBtele'] = ['usb']
 

def checkDomainStrings(domainStrings):
    for dstring in domainStrings:
        if dstring not in available_domains:
            logger.error("Sorry, "+dstring+" is not an available domain string. See DomainUtils.available_domains")


class DomainUtils():
    '''Utilities for ontology queries
    
        :param None:
    '''
    def __init__(self, domainString, rootIn=None):

        global root
        if rootIn is not None:  # just used when called by SemI parser without a config file
            root = rootIn
        if Settings.config is not None:
            if Settings.config.has_option('DEFAULT','root'):
                root = Settings.config.get('DEFAULT','root')

        #------------------------------ 
        #configlist = []
        #if Settings.config.has_section('dbase'):
        #    for opt in Settings.config.options('dbase'):
        #        if opt not in configlist and opt not in Settings.config.defaults():
        #            logger.error('Invalid config: ' + opt)
        #------------------------------

        self.domainString = domainString
        #raw_input
        logger.debug('DomainUtils.py XXXX -- '+domainString)
        self.ontology = self.load_ontology() 
        self.db = self.load_db()
        self.set_domains_slots()
        # For conditional goal generation:
        self.PROB_MASS_OVER_CONDITIONALS = 0.9

    def set_domains_slots(self):
        self.sorted_system_requestable_slots = self.ontology["system_requestable"] 
        self.sorted_system_requestable_slots.sort()
        self.informable_slots = self.ontology["informable"].keys()
        return

    def load_ontology(self):
        """
        """
        ontology_fname = root + ont_db_pairs[self.domainString]['ontology']
        logger.info('Loading ontology: '+ontology_fname)
        try:
            ontology = json.load(open(ontology_fname))
        except IOError:
            logger.error("No such file or directory: "+ontology_fname+". Probably <root> is not set in config/cmd-line.")
        return ontology

    def load_db(self):
        """
        """
        db_fname = root + ont_db_pairs[self.domainString]['database']
        logger.info('Loading database: '+db_fname)
        try:
            db = DataBase.DataBase(db_fname)
        except IOError:
            logger.error("No such file or directory: "+db_fname+". Probably <root> is not set in config or cmd line.")
        return db

    def getRandomValueForSlot(self, slot, nodontcare=False, notthese=[], conditional_values=[]):
        '''
    
        :param slot: (str)
        :param nodontcare: (bool)
        :param notthese: (list)
        '''
        if slot == 'type':
            #TODO - still think need to think about how "type" slot is used
            return self.ontology['type']

        if slot not in self.ontology['informable']:
            return None

        candidate = copy.deepcopy(self.ontology['informable'][slot])
        if len(candidate) == 0:
            logger.warning("candidates for slot "+slot+" should not be empty")
        if not nodontcare:
            candidate += ['dontcare']
        candidate = list(set(candidate) - set(notthese))
        # TODO - think should end up doing something like if candidate is empty - return 'dontcare' 
        if len(candidate) == 0:
            return 'dontcare'
        # Conditionally sample a goal based on already generated goals in other domains  
        conditional_sample_prob = self.get_sample_prob(candidate,conditional_values)

        return Settings.random.choice(candidate, p=conditional_sample_prob)

    def get_sample_prob(self, candidate, conditional_values): 
        """Sets a prob distribution over the values in *candidate* (which could be slots, or values with a slot)
        - assigns larger probabilities to things within the *conditional_values* list

        :param candidate: (list) of strings
        :param conditional_values: (list) of strings
        :returns: numpy vector with prob distribution
        """
        conditional_sample_prob = None
        if len(conditional_values):
            prob_mass_per_cond = self.PROB_MASS_OVER_CONDITIONALS/float(len(conditional_values))
            conditional_sample_prob = np.zeros(len(candidate))
            for cond in conditional_values:
                conditional_sample_prob[candidate.index(cond)] += prob_mass_per_cond
            # and normalise (ie fix zero elements)
            prob_mass_per_non_cond = (1.0-self.PROB_MASS_OVER_CONDITIONALS)/\
                    float(len(conditional_sample_prob)-len(conditional_sample_prob[np.nonzero(conditional_sample_prob)]))
            conditional_sample_prob[conditional_sample_prob==0] = prob_mass_per_non_cond 
            if not np.isclose(1.0, math.fsum(conditional_sample_prob)): 
                logger.warning("Sampling prob distrib not normalised.sums to: "+str(math.fsum(conditional_sample_prob)))
                return None
        return conditional_sample_prob

    def getValidSlotsForTask(self):
        '''
        :param None:
        :returns: (list) with goal slot strings 
         
        '''
        goalslots = self.ontology['system_requestable']
        if len(goalslots) < 1:
            logger.error('Number of goal constraints == 0')
        return goalslots

    def getValidRequestSlotsForTask(self):
        '''
        :param None:
        :returns: (list) with user requestable goal slot strings 
        
        .. todo::
            should be extended to cover arbitrary domains and ontologies
        '''
        A = self.ontology['requestable']
        B = self.ontology['system_requestable']
        request_slots = list(set(A)-set(B))
        return request_slots


    def getSlotsToExpress(self, slot, value):
        '''
        :param slot:
        :param value:
        :returns: List of slot names that should be conveyed for
                 the given abstract slot-value pair.
        '''
        result = []
        if value == '':
            result.append(slot)

        # logger.warning('DomainUtils: not completely implemented')
        return [slot]
        rules = ruletable.findClassByTerm(slot)

        if not rules:
            return result

        keytype = getKeyTypeForSlot(slot, rules[0].subclass)
        if keytype == 'structKey':
            argrules = ruletable.findClassBInst(slot)
            if argrules and argrules[0].args and value != 'dontcare':
                result = getSlotsForSubclass(value)

        if not result:
            result.append(slot)

        return result

    #def getRandomValueForTask():
    #    pShouldReturn = False
    #    filteredTaskList = []

    def is_valid_request(self, request_type, slot):
        # TODO
        logger.debug('Currently not implemented: always return True.')
        return True

    def is_implied(self, slot, value):
        logger.warning('Currently not implemented: always return False.')
        return False

    def getPolicyFiles(self):
        policy_file = ""
        if Settings.config.has_option("policy_"+self.domainString,"policyfile"):
            policy_file = Settings.config.get("policy_"+self.domainString,"policyfile")
        return policy_file
       

#END OF FILE
