'''
TopicManager.py - 
==========================================================================

Author: David Vandyke  (Copyright CUED Dialogue Systems Group 2015)

.. seealso:: CUED Imports/Dependencies: 

    import :class:`DMan` |.|
    import :class:`DomainUtils` |.|
    import :class:`Settings` |.|
    import :class:`ContextLogger` 

************************

'''
__author__ = "davidvandyke"
import Settings
import DMan
import DomainUtils
import ContextLogger
logger = ContextLogger.getLogger('')


class GenericDM():
    """Generic/Welcoming Dialogue Manager.
    """
    def __init__(self):
        pass

    def act_on(self,sys_act,hyps, constraints=None):
        """
        In case system takes first turn - Topic manager will just greet the user 
        """
        return 'hello()' 

    def startLearningEpisode(self, episodeNum):
        pass

    def restart(self):
        pass



class TopicManager():
    # TODO
    """
    TODO details
    """
    def __init__(self):
        self.domainManagers = dict.fromkeys(DomainUtils.available_domains, None)
        self.domainManagers['topicmanager'] = GenericDM()
        self.operatingDomain = 'topicmanager'  # TODO - Currently can only be one domain operating

    def restart(self):
        self.operatingDomain = 'topicmanager'
        self.in_present_dialog = []  # no domains involved in present dialog yet.
        self.prev_domain_constraints = dict.fromkeys(DomainUtils.available_domains) # used to facilate cond. behaviour
        for dstring in self.domainManagers.keys():
            if self.domainManagers[dstring] is not None: 
                self.domainManagers[dstring].restart()

    def _print_belief(self, dstring):
        """Just a **Debug** function
        """
        if self.domainManagers[dstring].beliefs.prevbelief is None:
            raw_input("Beliefs is None")
            return
        for slot,value in self.domainManagers[dstring].beliefs.prevbelief["beliefs"].iteritems():
            print value
            print slot
        raw_input("hold and check beliefs in "+dstring)

    def track_topic(self, userAct=None, userAct_hyps=None, domainString=None, previousDomainString=None, episodeNum=1):
        """details

        :param:
        :returns: either None or a list of conditional constraints
        """
        # TODO for now - just cheat and pass 'domain' directly to TopicManager
        # should be doing some sort of inference on user act or ASR n-best list in order to determine which domain(s)
        # are active.
        # FOR NOW ONLY ONE DOMAIN CAN BE ACTIVE IN EACH TURN.
        if domainString is not None:
            # The Bootup part - when first launching a new dialogue manager:
            if domainString not in self._currentlyActive():
                logger.info('Launching Dialogue Manager for domain: '+domainString)
                return self.bootup(domainString, previousDomainString, episodeNum)
            elif self.operatingDomain != domainString:
                # then we are switching domains: 
                if domainString not in self.in_present_dialog:
                    # note that this domain is now involved in current dialog:
                    self.in_present_dialog.append(domainString)
                    logger.info('Handing control to running - '+domainString+' - dialogue manager')
                    self.operatingDomain = domainString
                    # Start learning episode - (will pass if HDC or not learning): 
                    self.startLearningEpisode(episodeNum) 
                    return self._conditionally_init_new_domains_belief(previousDomainString)
                else:
                    # moving back to a domain that occured in an earlier turn of dialog. 
                    raw_input("wont see just now- until change sim user behaviour to move on-come back")
                    logger.info('Handing control <BACK> to running - '+domainString+' - dialogue manager')
                    self.operatingDomain = domainString
            else:
                logger.info('Domain '+domainString+' is both already running and has control') 
        return
    
    def _conditionally_init_new_domains_belief(self, previousDomainString):
        """
        """
        if previousDomainString is not None and Settings.CONDITIONAL_BEHAVIOUR:
            #TODO - delete: raw_input("previous domain was not none - in topice tracker")
            #-- If just starting this domain in this dialog: Get count80 slot=value pairs from previous
            #- domains in order to initialise the belief state of the new domain (reflecting dialogs history
            #- and likelihood that similar values will be desired if there are slot overlaps.
            # 1. get 'count80' slot=values:
            self.prev_domain_constraints[previousDomainString] = \
                    self.domainManagers[previousDomainString].getBelief80_pairs()
            # 2. initialise belief in (this dialogs) new domain:
            return self.domainManagers[self.operatingDomain].get_conditional_constraints(self.prev_domain_constraints)  
        else:
            return


    def _currentlyActive(self):
        """Pertains to whole simulate run over multiple dialogs. Has the dialog manager for this domain been booted up?
        """
        return [domain for domain, value in self.domainManagers.iteritems() if value is not None]

    def bootup(self, domainString, previousDomainString=None, episodeNum=1):
        """
        """
        # also fire up the DMUtils - pass the slots too below...
        domain_utils = DomainUtils.DomainUtils(domainString=domainString)
        self.domainManagers[domainString] = DMan.DMan(domainUtil = domain_utils)
        self.domainManagers[domainString].restart()
        self.operatingDomain = domainString
        self.startLearningEpisode(episodeNum)
        # and note that this domain is now involved in current dialog:
        self.in_present_dialog.append(domainString)
        return self._conditionally_init_new_domains_belief(previousDomainString)

    def startLearningEpisode(self, episodeNum):
        """
        """
        # TODO - check this - assumes only one domain ACTIVE - via self.operatingDomain.
        self.domainManagers[self.operatingDomain].startLearningEpisode(episodeNum)


    def recordReward(self, reward):
        # TODO - implement this as appropriate. 
        # for now - just pass it to the active DMan. 
        self.domainManagers[self.operatingDomain].recordReward(reward)
        """
        for dman in self.domainManagers.values():
            if dman is not None:
                dman.recordReward(reward)
                break
        """

    def act_on(self, sys_act, hyps, constraints=None):
        # TODO - this will need fixing if multiple domains are to run simultaneously, yet we must still only return
        # a single dialogue act (string)
        #logger.info('active domain is: '+self.operatingDomain)
        next_sys_act = self.domainManagers[self.operatingDomain].act_on(sys_act, hyps, constraints)
        return next_sys_act
        """
        for domain, dman in self.domainManagers.iteritems():
            if dman is not None:
                sys_act = dman.act_on(sys_act, hyps)
                # TODO - fix to work with topic manager -- logger.debug(self.system.beliefs.str())
        return sys_act
        """

    #TODO -delete old interface/approach
    """
    def endLearningEpisode(self, final_reward):
        # TODO - implement this as appropriate. 
        # for now - just pass it to the active DMan. assume only a single domain is active. 
        self.domainManagers[self.operatingDomain].endLearningEpisode(final_reward) 
        for dman in self.domainManagers.values():
            if dman is not None:
                dman.endLearningEpisode(final_reward)
                break 
    """
    
    def endLearningEpisode(self, domainRewards):
        """
        Finalise learning in all domains by passing final domain reward. 
        :param:
        :returns:
        """
        for dstring in self.domainManagers.keys():
            if self.domainManagers[dstring] is not None and dstring is not 'topicmanager':
                domains_reward = domainRewards[dstring]
                if domains_reward is not None: 
                    self.domainManagers[dstring].endLearningEpisode(domains_reward) 
                else:
                    logger.debug("Final reward in domain: "+dstring+" is None - Should mean domain wasnt used in dialog")
        return

    def savePolicy(self):
        """
        """
        # TODO - implement this as appropriate. 
        self.domainManagers[self.operatingDomain].savePolicy()

        for dstring in self.domainManagers.keys():
            if dstring is not 'topicmanager' and self.domainManagers[dstring] is not None:
                self.domainManagers[dstring].savePolicy()
        return 



# END OF FILE
