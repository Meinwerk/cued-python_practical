'''
RewardComputer.py - Calculates per-turn reward
===============================================

Authors: Dongho Kim, David Vandyke  (Copyright CUED Dialogue Systems Group 2015)

   
    .. warning:: 
        In current system usage this module is not used.
        Typically we resort to giving -1 per-turn always and the 
        UserSimulator will calculate an objective success check. 

**Basic Usage**:
    >>> import RewardComputer
    >>> rc = RewardComputer.RewardComputer()

Initialise for new dialog by:
    >>> rc.restart()

and get the reward after each turn of the dialog by:
    >>> rc.get_reward(prev_consts, requests, sys_act, user_act)

**Relevant config variables**  (values are defaults)::

    [eval]
    rewardvenuerecommended=100
    penaliseallturns=False
    wrongvenuepenalty=4
    notmentionedvaluepenalty=4


.. seealso:: CUED Imports/Dependencies: 

    import :class:`Settings` |.|
    import :class:`ContextLogger`


************************

'''

__author__ = "donghokim, davidvandyke"

import Settings
import DomainUtils
import ContextLogger
logger = ContextLogger.getLogger(__name__)


class RewardComputer():
    """Class for per-turn rewards based on dialog events and known task """
    def __init__(self, domainString):
        
        #DomainUtils() instance, which accesses ontology and database.
        self.domainUtil = DomainUtils.DomainUtils(domainString=domainString)

        configs = []
        # self.reward_every_turn = True
        # if Settings.config.has_option("eval", "rewardeveryturn"):
        #     configs.append('rewardeveryturn')
        #     self.reward_every_turn = Settings.config.getboolean('eval', 'rewardeveryturn')
        self.reward_venue_recommended = 100
        if Settings.config.has_option('eval', 'rewardvenuerecommended'):
            configs.append('rewardvenuerecommended')
            self.reward_venue_recommended = Settings.config.getint('eval', 'rewardvenuerecommended')
        self.penalise_all_turns = False
        if Settings.config.has_option('eval', 'penaliseallturns'):
            configs.append('penaliseallturns')
            self.penalise_all_turns = Settings.config.getboolean('eval', 'penaliseallturns')
        self.wrong_venue_penalty = 4
        if Settings.config.has_option('eval', 'wrongvenuepenalty'):
            configs.append('wrongvenuepenalty')
            self.wrong_venue_penalty = Settings.config.getint('eval', 'wrongvenuepenalty')
        self.not_mentioned_value_penalty = 4
        if Settings.config.has_option('eval', 'notmentionedvaluepenalty'):
            configs.append('notmentionedvaluepenalty')
            self.not_mentioned_value_penalty = Settings.config.getint('eval', 'notmentionedvaluepenalty')

        self.restart()

        if Settings.config.has_section('eval'):
            for opt in Settings.config.options('eval'):
                if opt not in configs and opt not in Settings.config.defaults():
                    logger.error('Invalid config: '+opt)

        
    def restart(self):
        """ Initialise variables (i.e. start dialog with: success=False, venue recommended=False, and 'dontcare' as \
                the only mentioned value in each slot)  
    
        :param: None
        :returns: None

        """
 
        self.venue_recommended = False
        self.success = False
        self.mentioned_values = {}      # {slot: set(values), ...}
        for slot in self.domainUtil.ontology['system_requestable']:
            self.mentioned_values[slot] = set(['dontcare'])

    #def get_reward(self, prev_consts, requests, sys_act, user_act):  TODO - delete old interface, update docstring
    def get_reward(self, um):
        """calculates the turn level reward given the context (input arguments)

            :param prev_consts: (list)  task constraints as 3-tuples, e.g. (u'food', '=', u'british')  
            :param requests: (dict)  requested slots, e.g. {'name': None, 'addr': None} 
            :param sys_act: (class :class:`DiaAct.DiaAct`)  system action, e.g. inform(name=X, food=Y)
            :param user_act: (class :class:`DiaAct.DiaAct`)  user action, e.g. request(area) 
            :returns: calculated reward (int)

        """
        # unpack input user model um.
        prev_consts = um.prev_goal.constraints 
        requests = um.goal.requests
        sys_act = um.lastSysAct
        user_act = um.lastUserAct

        # Immediate reward for each turn.
        reward = -self.penalise_all_turns

        # After success, just return -penalise_all_turns
        if self.success:
            return reward

        # Check if the most recent venue satisfies constraints.
        name = sys_act.get_value('name', negate=False)
        if name not in ['none', None]:
            # Venue is recommended.
            possible_entities = self.domainUtil.db.entity_by_features(prev_consts)
            match = name in [e['name'] for e in possible_entities]
            if match:
                # Success except if the next user action is reqalts.
                if user_act.act != 'reqalts':
                    logger.debug('Correct venue is recommended.')
                    self.venue_recommended = True   # Correct venue is recommended.
                else:
                    logger.debug('Correct venue is recommended but the user has changed his mind.')
            else:
                # Previous venue did not match.
                logger.debug('Venue is not correct.')
                self.venue_recommended = False
                reward -= self.wrong_venue_penalty

        # If system inform(name=none) but it was not right decision based on wrong values.
        if name == 'none' and sys_act.has_conflicting_value(prev_consts):
            reward -= self.wrong_venue_penalty

        # Check if the system used slot values previously not mentioned for 'select' and 'confirm'.
        not_mentioned = False
        if sys_act.act in ['select', 'confirm']:
            for slot in self.domainUtil.ontology['system_requestable']:
                values = set(sys_act.get_values(slot))
                if len(values - self.mentioned_values[slot]) > 0:
                    # System used values which are not previously mentioned.
                    not_mentioned = True
                    break

        if not_mentioned:
            reward -= self.not_mentioned_value_penalty

        # If the correct venue has been recommended and all requested slots are filled,
        # check if this dialogue is successful.
        if self.venue_recommended and None not in requests.values():
            self.success = True
            reward += self.reward_venue_recommended

        # Update mentioned values.
        self._update_mentioned_value(sys_act)
        self._update_mentioned_value(user_act)
        return reward

    def _update_mentioned_value(self, act):
        """internal, called by :meth:`RewardComputer.get_reward` for both sys and user acts to update values mentioned in dialog

            Args:
                *act* (class :class:`DiaAct.DiaAct`) : sys or user dialog act
            Returns:
                *None*
            
        """
        for item in act.items:
            if item.slot in self.domainUtil.ontology['system_requestable'] and item.val not in [None, '**NONE**', 'none']:
                self.mentioned_values[item.slot].add(item.val)



# END OF FILE
