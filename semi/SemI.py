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
SemI.py - Semantic input parser
===================================

Authors: Dongho Kim, David Vandyke  (Copyright CUED Dialogue Systems Group 2015)

.. seealso:: CUED Imports/Dependencies: 
        **None**

.. warning::
        No semantic parser is implemented. 
        Pass through semantic input parsing is only thing implemented here.  

************************

'''

__author__ = "donghokim, davidvandyke"
import re,os,sys
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.sys.path.insert(0,parentdir) 
import ContextLogger
import DomainUtils
import Settings
logger = ContextLogger.getLogger('')

def external_texthub_decode(obs):
    """Same as decode(), but user can enter a switch(domain="DOMAINTAG") semantic act. NB must use "" quotes.

    :param obs: (str)
    :returns: (str) obs and (str or None) for domainTag
    """
    # created new function, rather than execute if (detection) statement each time in simulate
    domainTag = None
    if len(obs) == 1:
        if "switch(" in obs[0][0]:
            return [], obs[0][0].split('"')[1] 
    return obs, domainTag



class PassthroughSemI():
    '''**Does nothing** - simply pass observation directly through (on assumption that observation was a semantic act input by a texthub user) -- hence is domain independent and doesn't need a manager
    '''
    def decode(self, obs):
        '''
        :param obs: (str) 
        :returns: (str) **EXACT** obs as was input
        '''
        return obs

    def texthub_decode(self,obs):
        """Same as decode(), but user can enter a switch(domain="DOMAINTAG") semantic act. NB must use "" quotes.

        :param obs: (str)
        :returns: (str) obs and (str or None) for domainTag
        """
        return external_texthub_decode(obs)  # non-class member


class RegexSemI():
    """
    """
    def __init__(self,domainTag):
        self.domain_tag = domainTag
        sys.path.append("semi/")
        parser_module = __import__("RegexSemI_"+self.domain_tag, fromlist=["RegexSemI_"+self.domain_tag]) 
        self.parser = getattr(parser_module, "RegexSemI_"+self.domain_tag)()

    def decode(self, obs):
        """
        """
        return self.parser.decode(obs)


class SemIManager():
    """
    """
    def __init__(self):
        self.semiManagers = dict.fromkeys(DomainUtils.available_domains)
        self.semiTypes = dict.fromkeys(DomainUtils.available_domains)
        self.active_domain = None


    def _update_active_domain(self, activeDomain):
        """
        """
        self.active_domain = activeDomain
        if self.semiManagers[self.active_domain] is None:
            self._load_domains_semi(dstring=self.active_domain)
   
    def _get_semi_type(self, dstring=None): 
        """Get from the config file the SemI choice of method for this domain
        """
        self.semiTypes[dstring] = 'PassthroughSemI'
        if Settings.config.has_option('hub_'+dstring, 'semi'):
            self.semiTypes[dstring] = Settings.config.get('hub_'+dstring, 'semi')


    def _load_domains_semi(self,dstring=None):
        """
        """
        # Get from config the choosen SemI method for this domain:
        self._get_semi_type(dstring)

        # And load that method for the domain:
        if self.semiTypes[dstring] == 'PassthroughSemI':
            self.semiManagers[dstring] = PassthroughSemI()
        elif self.semiTypes[dstring] == 'RegexSemI':
            self.semiManagers[dstring] = RegexSemI(domainTag=dstring)
        else:
            logger.warning('Invalid SemI: %s. Using PassthroughSemI.' % self.semiTypes[dstring])
            self.semiManagers[dstring] = PassthroughSemI()

    def decode(self, obs):
        """
        """
        return self.semiManagers[self.active_domain].decode(obs)

    def texthub_decode(self,obs):
        """Same as decode(), but user can enter a switch(domain="DOMAINTAG") semantic act. NB must use "" quotes.

        :param obs: (str)
        :returns: (str) obs and (str or None) for domainTag
        """
        domainTag = None
        tempObs, domainTag =  external_texthub_decode(obs)  # non-class member 
        if domainTag is None:
            return self.decode(obs), domainTag  #TODO - may need changing if we add probs with obs
        else:
            self._update_active_domain(activeDomain=domainTag)
            return tempObs, domainTag



#END OF FILE
