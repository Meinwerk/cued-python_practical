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
UserSimulator.py -combines simulated components into functional simulator 
==========================================================================

Authors: Dongho Kim, David Vandyke  (Copyright CUED Dialogue Systems Group 2015)

**Basic Usage**: 
    >>> import UserSimulator
    >>> simulator = UserSimulator.CuedUserSimulator()  

Then set it up for a dialogue by:
    >>> simulator.restart()

Obtain user response by:
    >>> user_act = simulator.act_on(sys_act)

A turn level reward can be obtained by:
    >>> reward = simulator.get_reward() 

.. seealso:: CUED Imports/Dependencies: 

    import :class:`UserModel` |.|
    import :class:`RewardComputer` |.|
    import :class:`DiaAct` |.|
    import :class:`ContextLogger`

************************

'''

__author__ = "donghokim, davidvandyke"
import copy

import UserModel
import RewardComputer
import DiaAct
import DomainUtils
import Settings
import ContextLogger
logger = ContextLogger.getLogger('')


class CuedUserSimulator():
    '''User Simulator for a single domain. Comprised of a behaviour component: :class:`UserModel` only. Originally contained the evaluation mechanism as well via :class:`RewardComputer`, but this has been moved to the :class:`Evaluation` module. 

    :param None:
    '''
    def __init__(self, domainString):
        # User model
        self.um = UserModel.UM(domainString)
 
    def restart(self, otherDomainsConstraints):
        '''Resets all components (**User Model**)

        :param otherDomainsConstraints: (list) of domain goal tuples (slot=val)
        :returns: None
        '''
        self.um.init(otherDomainsConstraints) 
        
    def act_on(self, sys_act_string):
        '''Thru the UserModel member, receives the system action and then responds.

        :param sys_act_string: (unicode str) system action
        :returns: (str) user action
        '''
        sys_act = DiaAct.DiaAct(sys_act_string)
        self.um.receive(sys_act)
        user_act = self.um.respond()
        return user_act.to_string()


class SimulatedUsersManager():
    """The multidomain simulated user, which is made up of a dictionary of simulated users indexed by domain. 

        :param (list): of domain strings
    """
    def __init__(self, domainStrings):
        assert(isinstance(domainStrings,list))
        self.possible_domains = copy.copy(domainStrings)
        self.domainSimulatedUsers = dict.fromkeys(DomainUtils.available_domains, None)
        #TODO - not sure what is best approach: set by length of allowed partner domains -- 
        self.INCLUDE_DOMAIN_PROB = 0.6  # TODO make this a config setting?
        self.MAX_DOMAINS_PER_DIALOG = 3
        if Settings.config.has_option("DEFAULT","maxdomainsperdialog"):
            self.MAX_DOMAINS_PER_DIALOG = Settings.config.getint("DEFAULT","maxdomainsperdialog") 


    def set_allowed_codomains(self, ROOTDOMAIN):
        """Sets member (list) *allowed_codomains* given a root domain name (ie the domain of the first constraint)
        Uses the hardcoded rules in :class:`DomainUtils` to do so. Also, based on determined allowed_codomains, sets
        the probability of each being included, independently.

        :param ROOTDOMAIN: (str) domain tag
        :returns: None  (but sets internal class member, **allowed_codomains**)
        """
        self.allowed_codomains = DomainUtils.ALLOWED_CODOMAIN_RULES[ROOTDOMAIN]
        #NB: These next few lines depend a little on hard coding of DomainUtils.ALLOWED_CODOMAIN_RULES
        if len(self.allowed_codomains) > 1:
            if isinstance(self.allowed_codomains[1],list):
                randindex = Settings.random.randint(0,len(DomainUtils.ALLOWED_CODOMAIN_RULES[ROOTDOMAIN]))
                self.allowed_codomains = DomainUtils.ALLOWED_CODOMAIN_RULES[ROOTDOMAIN][randindex]
        # based on the allowed_codomains, set the prob of each one independently being in the dialog:
        #self.INCLUDE_DOMAIN_PROB = min(0.3,1.0/len(self.allowed_codomains))
        return


    def sample_domains(self):
        """Randomly select a set of domains from those available. 
            The selected domains will be used by the simulated user over a single dialog.

        :param None:
        :returns: None
        """
        # sample from possible_domains
        self.using_domains = []
        self.using_domains.append(Settings.random.choice(self.possible_domains))  # must have at least 1 element 
        root_domain = self.using_domains[0] # the first chosen domain - will affect which codomains can be partnered with
        self.set_allowed_codomains(ROOTDOMAIN=root_domain)
        shuffled_possible_domains = list(self.possible_domains)
        Settings.random.shuffle(shuffled_possible_domains)

        for dstring in shuffled_possible_domains:
            if len(self.using_domains) == self.MAX_DOMAINS_PER_DIALOG:
                break
            if dstring not in self.allowed_codomains:
                continue
            if dstring in self.using_domains:
                continue
            if Settings.random.rand() < self.INCLUDE_DOMAIN_PROB:
               self.using_domains.append(dstring) 

        Settings.random.shuffle(self.using_domains) # list order is persistent. Simulated user will act in this order now. 
        logger.info('Order sim user will execute goals:'+str(self.using_domains))
        self.uncompleted_domains = list(self.using_domains)
        return

    def restart(self):
        """Restarts/boots up the selected domains simulated user components. Shuts down those running and not needed for 
            the next dialog.

        :param None:
        :returns: None
        """ 
        # sample domain for this dialog and randomise order:
        self.sample_domains()

        # reset domain simulators:
        otherDomainsConstraints = []  # used to conditionally generate domain goals

        for dstring in self.using_domains: # doing this way to generate goals/behaviour in an order.
            # fire up or check if it is running
            if self.domainSimulatedUsers[dstring] is None:
                self.domainSimulatedUsers[dstring] = CuedUserSimulator(domainString=dstring)
            self.domainSimulatedUsers[dstring].restart(otherDomainsConstraints)
            # DEBUG prints to inspect goals we have generated:
            logger.debug(str(self.domainSimulatedUsers[dstring].um.goal))
            logger.debug(str(self.domainSimulatedUsers[dstring].um.goal.copied_constraints))
            logger.debug(str(self.domainSimulatedUsers[dstring].um.hdcSim.agenda.agenda_items))
            logger.debug("DOMAIN-----"+dstring)
            #raw_input('goal and agenda for domain '+dstring)
            if Settings.CONDITIONAL_BEHAVIOUR:
                otherDomainsConstraints += self.domainSimulatedUsers[dstring].um.goal.constraints
             

        for dstring in self.possible_domains:  #unlike DMan, no memory here. Fine to actually `kill' domains not using 
            if dstring not in self.using_domains:
                self.domainSimulatedUsers[dstring] = None 
        return 

    def act_on(self, sys_act):
        """
        """
        # TODO - this is just a start. lots needs thinking about here.
        # -- needs to return the current simulation domain explictly for now
        # cheat for now: only use one domain -- dstring is a cheat
        # May not be a cheat - can use this information for error simulation. Just don't use it for tracking etc, even
        # though it is there. 
        logger.debug('simulated users uncompleted domains:'+str(self.uncompleted_domains))
        for dstring in self.using_domains:
            # TODO - check this, may need to use an ordered dict.
            if dstring in self.uncompleted_domains:
                user_act = self.domainSimulatedUsers[dstring].act_on(sys_act)
                if 'bye(' in user_act:
                    sys_act = 'hello()'
                    self.uncompleted_domains.remove(dstring)
                    if len(self.uncompleted_domains):
                        continue
                    else:
                        break
                else:
                    break
        return  user_act, dstring
    
# END OF FILE
