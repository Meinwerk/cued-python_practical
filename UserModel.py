'''
UserModel.py - goal, agenda inventor for sim user 
====================================================

Authors: Dongho Kim, David Vandyke  (Copyright CUED Dialogue Systems Group 2015)

.. seealso:: CUED Imports/Dependencies: 
    
    import :class:`DiaAct` |.|
    import :class:`dact` |.|
    import :class:`UMHdcSim` |.|
    import :class:`DomainUtils` |.|
    import :class:`Settings` |.|
    import :class:`ContextLogger`

.. warning::
        documentation not complete

************************

'''
__author__ = "donghokim, davidvandyke"
import copy

import DiaAct
import dact
import UMHdcSim
import DomainUtils
import Settings
import ContextLogger
logger = ContextLogger.getLogger('')


class UMAgenda():
    '''Agenda of :class:`DiaAct` acts corresponding to a goal.
    
    :param domain: (instance) of :class:`DomainUtils`
    '''
    def __init__(self, domainUtil):
        self.domainUtil = domainUtil
        self.agenda_items = []  # Stack of DiaAct
        self.rules = None
        # HDC probs on how simuser will conditionally behave: values are upper limits of ranges uniform sample falls in
        self.NOT_MENTION = 1.0 # default - this value doesnt actually matter
        self.LEAVE_INFORM = 0.4
        self.CONFIRM = -1.0  # doesn't make sense actually to change inform(X=Y) to a confirm() act.
        # ONE OTHER OPTION IS TO APPEND constraint into another inform act so it is inform(X=Y,A=B)

    def init(self, goal):
        """
        Initialises the agenda by creating DiaActs corresponding to the
        constraints in the goal G. Uses the default order for the
        dialogue acts on the agenda: an inform act is created for
        each constraint. Finally a bye act is added at the bottom of the agenda.
        
        :param goal: 
               
        .. Note::
            No requests are added to the agenda.
        """
        self.agenda_items = []
        self.append_dact_to_front(DiaAct.DiaAct('inform(type="%s")' % goal.request_type))

        for const in goal.constraints:
            slot = const.slot
            value = const.val
            if slot == 'method':
                continue

            do_not_add = False
            dia_act = DiaAct.DiaAct('inform()')
            slots = self.domainUtil.getSlotsToExpress(slot, value)

            for s in slots:
                val = goal.get_correct_const_value(s)
                if val is not None:
                    dia_act.append(slot, val)
                if len(slots) == 1 and self.contains(s, val):
                    do_not_add = True
                elif len(slots) > 1:
                    # Slot value pair might already be in other act on agenda: remove that one
                    self.filter_acts_slot(s)

            if not do_not_add:
                self.append_dact_to_front(dia_act)

        # CONDITIONALLY INIT THE AGENDA:
        if len(goal.copied_constraints): # dont need Settings.CONDITIONAL_BEHAVIOUR - list will be empty as appropriate
            self._conditionally_init_agenda(goal)
          
        # Finally append a bye() act to complete agenda:
        self.append_dact_to_front(DiaAct.DiaAct('bye()'))
        return

    def _conditionally_init_agenda(self, goal):
        """Use goal.copied_constraints -- to conditionally init Agenda.
        Probabilistically remove/alter the agenda for this constraint then:

        :param:
        :returns:
        """

        for dact in goal.copied_constraints:
            print dact.slot, dact.op, dact.val
            uniform_sample = Settings.random.uniform()
            print uniform_sample
            if uniform_sample < self.CONFIRM:
                # TODO - remove/change this - 
                # Decided this doesn't make sense - (so set self.CONFIRM=0) - info is in belief state, that is enough.
                logger.info("changing inform() act to a confirm() act")
                self.replace_acts_slot(dact.slot, replaceact="confirm") 
            elif uniform_sample < self.LEAVE_INFORM:
                pass
            else:
                logger.info("removing the inform() act and not replacing with anything.") 
                self.filter_acts_slot(dact.slot)
        return


    def contains(self, slot, value, negate=False):
        '''Check if slot, value pair is in an agenda dialogue act

        :param slot:
        :param value:
        :param negate: (bool) 
        :returns: (bool) slot, value is in an agenda dact?
        '''
        for dact in self.agenda_items:
            if dact.contains(slot, value, negate):
                return True
        return False

    def get_agenda_with_act(self, act):
        '''agenda items with this act
        :param act: (str) dialogue act 
        :return: (list) agenda items
        '''
        items = []
        for ait in self.agenda_items:
            if ait.act == act:
                items.append(ait)
        return items

    def get_agenda_with_act_slot(self, act, slot):
        '''
        :param act: (str) dialogue act
        :param slot: (str) slot name
        :return: (list) of agenda items
        '''
        items = []
        for ait in self.agenda_items:
            if ait.act == act:
                for item in ait.items:
                    if item.slot == slot:
                        items.append(ait)
                        break
        return items

    def replace_acts_slot(self, slot, replaceact="confirm"):
        """
        """
        actindex = None
        for ait in self.agenda_items:
            if len(ait.items) == 1:
                if ait.items[0].slot == slot:
                    print ait.act
                    print ait.items
                    ait.act = replaceact
                    print ait
                    raw_input('going to change this to confirm')


    def filter_acts_slot(self, slot):
        '''
        Any acts related to the given slot are removed from the agenda.
        :param slot: (str) slot name
        :return: None
        '''
        deleted = []
        for ait in self.agenda_items:
            if ait.act in ['inform', 'confirm', 'affirm'] and len(ait.items) > 0:
                if len(ait.items) > 1:
                    logger.error('Assumes all agenda items have only one semantic items: '+ait)
                for only_item in ait.items:
                    if only_item.slot == slot:
                        deleted.append(ait)

        for ait in deleted:
            self.agenda_items.remove(ait)

    def filter_constraints(self, dap):
        '''Filters out acts on the agenda that convey the constraints mentioned in the given dialogue act. Calls :meth:`filter_acts_slot` to do so. 

        :param dap:
        :returns: None
        '''
        if dap.act in ['inform', 'confirm'] or \
            (dap.act in ['affirm', 'negate'] and len(dap.items) > 0):
            for item in dap.items:
                self.filter_acts_slot(item.slot)

    def size(self):
        '''Utility func to get size of agenda_items list
        
        :returns: (int) length
        '''
        return len(self.agenda_items)

    def clear(self):
        '''
        Erases all acts on the agenda (empties list)
        
        :return: None
        '''
        self.agenda_items = []

    def append_dact_to_front(self, dact):
        '''Adds the given dialogue act to the front of the agenda

        :param (instance): dact
        :returns: None
        '''
        self.agenda_items = [dact] + self.agenda_items

    def push(self, dact):
        # if dact.act == 'null':
        #     logger.warning('null() in agenda')
        # if dact.act == 'bye' and len(self.agenda_items) > 0:
        #     logger.warning('bye() in agenda')
        self.agenda_items.append(dact)

    def pop(self):
        return self.agenda_items.pop()

    def remove(self, dact):
        self.agenda_items.remove(dact)


class UMGoal():
    '''Defines a goal within a domain

    :param patience: (int) user patience 
    '''
    def __init__(self, patience, domainUtil=None):
        self.constraints = []
        self.copied_constraints = []  # goals copied over from other domains. Used to conditionally create agenda.
        self.requests = {}
        self.prev_slot_values = {}
        self.patience = patience
        self.request_type = domainUtil.ontology['type']  #'restaurant'

        self.system_has_informed_name_none = False
        self.no_relaxed_constraints_after_name_none = False

    def clear(self, patience, domainUtil=None):
        self.constraints = []
        self.requests = {}
        self.prev_slot_values = {}
        self.patience = patience
        self.request_type = domainUtil.ontology['type']  #'restaurant'

        self.system_has_informed_name_none = False
        self.no_relaxed_constraints_after_name_none = False

    '''
    Methods for constraints.
    '''
    def set_copied_constraints(self, all_conditional_constraints):
        """Creates a list of dacts, where the constraints have come from earlier domains in the dialog.

        :param all_conditional_constraints: (dict) of all previous constraints (over all domains in dialog)
        :returns: None
        """
        for dact in self.constraints:
            slot,op,value = dact.slot,dact.op,dact.val
            if slot in all_conditional_constraints.keys():
                if len(all_conditional_constraints[slot]):
                    if value in all_conditional_constraints[slot]:
                        self.copied_constraints.append(dact)
        return

    def add_const(self, slot, value, negate=False):
        """
        """
        if not negate:
            op = '='
        else:
            op = '!='
        item = dact.DactItem(slot, op, value)
        self.constraints.append(item)

    def replace_const(self, slot, value, negate=False):
        self.remove_slot_const(slot)
        self.add_const(slot, value, negate)

    def contains_slot_const(self, slot):
        for item in self.constraints:
            # an error introduced here by dact.py __eq__ method: 
            #if item.slot == slot:
            if str(item.slot) == slot:
                return True
        return False

    def remove_slot_const(self, slot):
        copy_consts = copy.deepcopy(self.constraints)
        for item in copy_consts:
            if item.slot == slot:
                self.constraints.remove(item)

    def get_correct_const_value(self, slot, negate=False):
        '''
        :return: (list of) value of the given slot in user goal constraint.

        '''
        values = []
        for item in self.constraints:
            if item.slot == slot:
                if item.op == '!=' and negate or item.op == '=' and not negate:
                    values.append(item.val)

        if len(values) == 1:
            return values[0]
        elif len(values) == 0:
            return None
        logger.error('Multiple values are found for %s in constraint: %s' % (slot, str(values)))
        return values

    def get_correct_const_value_list(self, slot, negate=False):
        '''
        :return: (list of) value of the given slot in user goal constraint.
        '''
        values = []
        for item in self.constraints:
            if item.slot == slot:
                if (item.op == '!=' and negate) or (item.op == '=' and not negate):
                    values.append(item.val)
        return values

    def add_prev_used(self, slot, value):
        '''
        Adds the given slot-value pair to the record of previously used slot-value pairs.
        '''
        if slot not in self.prev_slot_values:
            self.prev_slot_values[slot] = set()
        self.prev_slot_values[slot].add(value)

    def add_name_constraint(self, value, negate=False):
        if value in [None, 'none']:
            return

        wrong_venues = self.get_correct_const_value_list('name', negate=True)
        correct_venue = self.get_correct_const_value('name', negate=False)

        if not negate:
            # Can have only one name= constraint.
            if correct_venue is not None:
                #logger.debug('Failed to add name=%s: already got constraint name=%s.' %
                #             (value, correct_venue))
                return

            # Adding name=value but there is name!=value.
            if value in wrong_venues:
                logger.debug('Failed to add name=%s: already got constraint name!=%s.' %
                             (value, value))
                return

            # Adding name=value, then remove all name!=other.
            self.replace_const('name', value)
            return

        # if not negate and not self.is_suitable_venue(value):
        #     logger.debug('Failed to add name=%s: %s is not a suitable venue for goals.' % (value, value))
        #     return

        if negate:
            # Adding name!=value but there is name=value.
            if correct_venue == value:
                logger.error('Failed to add name!=%s: already got constraint name=%s.' % (value, value))
                return

            # Adding name!=value, but there is name=other. No need to add.
            if correct_venue is not None:
                return

            self.add_const('name', value, negate=True)
            return

    # def is_correct(self, item):
    #     '''
    #     Check if the given items are correct in goal constraints.
    #     :param item: set[(slot, op, value), ...]
    #     :return:
    #     '''
    #     if type(item) is not set:
    #         item = set([item])
    #     for it in item:
    #         for const in self.constraints:
    #             if const.match(it):

    def is_satisfy_all_consts(self, item):
        '''
        Check if all the given items set[(slot, op, value),..] satisfies all goal constraints (conjunction of constraints).
        '''
        if type(item) is not set:
            item = set([item])
        for it in item:
            for const in self.constraints:
                if not const.match(it):
                    return False
        return True

    def is_completed(self):
        # If the user has not specified any constraints, return True
        if not self.constraints:
            return True
        if (self.system_has_informed_name_none and not self.no_relaxed_constraints_after_name_none) or\
                (self.is_venue_recommended() and self.are_all_requests_filled()):
            return True
        return False

    '''
    Methods for requests.
    '''
    def reset_requests(self):
        for info in self.requests:
            self.requests[info] = None

    def fill_requests(self, dact_items):
        for item in dact_items:
            if item.op != '!=':
                self.requests[item.slot] = item.val

    def are_all_requests_filled(self):
        '''
        :return: True if all request slots have a non-empty value.
        '''
        return None not in self.requests.values()

    def is_venue_recommended(self):
        '''
        Returns True if the request slot 'name' is not empty.
        :return:
        '''
        if 'name' in self.requests and self.requests['name'] is not None:
            return True
        return False

    def get_unsatisfied_requests(self):
        results = []
        for info in self.requests:
            if self.requests[info] is None:
                results.append(info)
        return results

    def __str__(self):
        result = 'constraints: ' + str(self.constraints) + '\n'
        result += 'requests:    ' + str(self.requests) + '\n'
        if self.patience is not None:
            result += 'patience:    ' + str(self.patience) + '\n'
        return result


class GoalGenerator():
    '''Generates domain specific goals for simulated user.

    :param domain: (instance) of :class:`DomainUtils`
    '''
    def __init__(self, domainUtil):
        self.domainUtil = domainUtil
        
        configlist = []
        self.UM_PATIENCE = 3
        if Settings.config.has_option('goalgenerator','patience'):
            configlist.append('patience')
            self.UM_PATIENCE = Settings.config.getint('goalgenerator','patience')
        self.MAX_VENUES_PER_GOAL = 4
        if Settings.config.has_option('goalgenerator','maxvenuespergoal'):
            self.MAX_VENUES_PER_GOAL = Settings.config.getint('goalgenerator','maxvenuespergoal')
        self.MIN_VENUES_PER_GOAL = 1

        self.MAX_CONSTRAINTS = 3
        if Settings.config.has_option('goalgenerator','maxconstraints'):
            self.MAX_CONSTRAINTS = Settings.config.getint('goalgenerator','maxconstraints')

        self.MAX_REQUESTS = 3
        if Settings.config.has_option('goalgenerator','maxrequests'):
            self.MAX_REQUESTS = Settings.config.getint('goalgenerator','maxrequests')
        self.MIN_REQUESTS = 1
        if Settings.config.has_option('goalgenerator','minrequests'):
            self.MIN_REQUESTS = Settings.config.getint('goalgenerator','minrequests')
        assert(self.MIN_REQUESTS > 0)
#        if Settings.config.has_option('GOALGENERATOR','MINVENUESPERGOAL'):
#            self.MIN_VENUES_PER_GOAL = int(Settings.config.get('GOALGENERATOR','MINVENUESPERGOAL'))
#        self.PERCENTAGE_OF_ZERO_SOLUTION_TASKS = 50
#        if Settings.config.has_option('GOALGENERATOR','PERCZEROSOLUTION'):
#            self.PERCENTAGE_OF_ZERO_SOLUTION_TASKS = int(Settings.config.get('GOALGENERATOR','PERCZEROSOLUTION'))
#        self.NO_REQUESTS_WITH_VALUE_NONE = False
#        if Settings.config.has_option('GOALGENERATOR','NOREQUESTSWITHVALUENONE'):
#            self.NO_REQUESTS_WITH_VALUE_NONE

        if self.MIN_VENUES_PER_GOAL > self.MAX_VENUES_PER_GOAL:
            logger.error('Invalid config: MIN_VENUES_PER_GOAL > MAX_VENUES_PER_GOAL')

        if Settings.config.has_section('goalgenerator'):
            for opt in Settings.config.options('goalgenerator'):
                if opt not in configlist and opt not in Settings.config.defaults():
                    logger.error('Invalid config: ' + opt)

        # self.nGoalsGenerated = 0
        # self.nZeroSolutionGoalsGenerator = 0
       
    def _set_other_domains_constraints(self, otherDomainsConstraints):
        """Simplest approach for now: just look for slots with same name 
        """
        # Get a list of slots that are valid for this task.
        valid_const_slots = self.domainUtil.getValidSlotsForTask() 
        self.conditional_constraints = {slot: [] for slot in valid_const_slots}

        if not Settings.CONDITIONAL_BEHAVIOUR:
            self.conditional_constraint_slots = []
            return

        for const in otherDomainsConstraints:
            if const.slot in valid_const_slots and const.val != "dontcare": #TODO think dontcare should be dealt with diff 
                # issue is that first domain may be dontcare - but 2nd should be generated conditioned on first.
                if const.op == "!=":
                    continue
                if const.val in self.domainUtil.ontology['informable'][const.slot]: #make sure value is valid for slot
                    self.conditional_constraints[const.slot] += [const.val]  
        self.conditional_constraint_slots = [s for s,v in self.conditional_constraints.iteritems() if len(v)]
        return


    def init_goal(self, otherDomainsConstraints):
        '''
        Initialises the goal g with random constraints and requests

        :param otherDomainsConstraints: (list) of constraints from other domains in this dialog which have already had goals generated.
        :returns: (instance) of :class:`UMGoal`
        '''
        # clean/parse the domainConstraints list - contains other domains already generated goals:
        self._set_other_domains_constraints(otherDomainsConstraints)

        # Set initial goal status vars
        goal = UMGoal(self.UM_PATIENCE, domainUtil=self.domainUtil)
        logger.debug(str(goal))
        num_attempts_to_resample = 2000
        while True:
            num_attempts_to_resample -= 1
            # Randomly sample a goal (ie constraints):
            self._init_consts_requests(goal)
            # Check that there are venues that satisfy the constraints:
            venues = self.domainUtil.db.entity_by_features(goal.constraints)
            #logger.info('num_venues: %d' % len(venues))
            if self.MIN_VENUES_PER_GOAL < len(venues) < self.MAX_VENUES_PER_GOAL:
                break
            if num_attempts_to_resample == 0:
                logger.warning('Maximum number of goal resampling attempts reached.')

        # logger.warning('SetSuitableVenues is deprecated.')
        return goal
        
    def _init_consts_requests(self, goal):
        '''
        Randomly initialises constraints and requests of the given goal.
        '''
        goal.clear(self.UM_PATIENCE, domainUtil=self.domainUtil)

        # Randomly pick a task: bar, hotel, or restaurant (in case of TownInfo)
        #goal.add_const('type', self.domain.getRandomValueForSlot('type'))
        goal.request_type = self.domainUtil.getRandomValueForSlot('type')

        # Get a list of slots that are valid for this task.
        valid_const_slots = self.domainUtil.getValidSlotsForTask()
        
        # First randomly sample some slots from those that are valid: 
        random_slots = list(Settings.random.choice(valid_const_slots,
                                size=min(self.MAX_CONSTRAINTS, len(valid_const_slots)),
                                replace=False,
                                p=self.domainUtil.get_sample_prob(valid_const_slots,self.conditional_constraint_slots)))


        # Now randomly fill in some constraints for the sampled slots:
        for slot in random_slots:
            #TODO - delete what i think should be removed below: 'has' seems too hardcoded... 
            # I'm removing it: should be able to say dontcare for any slot i feel - djv27
            """
            if 'has' in slot:
                #goal.add_const(slot, True)
                goal.add_const(slot, self.domainUtil.getRandomValueForSlot(slot, nodontcare=True))
            else:
            """
            goal.add_const(slot, self.domainUtil.getRandomValueForSlot(slot, 
                                                            nodontcare=False,
                                                            conditional_values=self.conditional_constraints[slot]))
        
        # Add requests. Assume that the user always wants to know the name of the place
        goal.requests['name'] = None
        if self.MIN_REQUESTS == self.MAX_REQUESTS:
            n = self.MIN_REQUESTS -1  # since 'name' is already included
        else:
            n = Settings.random.randint(low=self.MIN_REQUESTS-1,high=self.MAX_REQUESTS)
        valid_req_slots = self.domainUtil.getValidRequestSlotsForTask()
        if n > 0:   # ie more requests than just 'name'
            choosen = Settings.random.choice(valid_req_slots, n,replace=False)
            for reqslot in choosen:
                goal.requests[reqslot] = None


class UM():
    '''Simulated user
    
    :param None:
    '''
    def __init__(self, domainString):
        domainUtil = DomainUtils.DomainUtils(domainString)
        self.generator = GoalGenerator(domainUtil)
        self.goal = None
        self.prev_goal = None
        self.hdcSim = UMHdcSim.UMHdcSim(domainUtil)
        self.lastUserAct = None
        self.lastSysAct = None
        
    def init(self, otherDomainsConstraints):
        '''
        Initialises the simulated user.
        1. Initialises the goal G using the goal generator.
        2. Populates the agenda A using the goal G.
        Resets all UM status to their defaults.

        :param otherDomainsConstraints: (list) of domain goals/constraints (slot=val) from other domains in dialog for which goal has already been generated.
        :returns None:
        '''
        self.goal = self.generator.init_goal(otherDomainsConstraints)
        logger.debug(str(self.goal))

        if Settings.CONDITIONAL_BEHAVIOUR:
            # now check self.generator.conditional_constraints list against self.goal -assume any values that are the same
            # are because they are conditionally copied over from earlier domains goal. - set self.goal.copied_constraints
            self.goal.set_copied_constraints(all_conditional_constraints=self.generator.conditional_constraints)

        self.lastUserAct = None
        self.lastSysAct = None
        self.hdcSim.init(self.goal)  #TODO - thurs - look at conditional generation of agenda as well.

    def receive(self, sys_act):
        '''
        This method is called to transmit the machine dialogue act to the user.
        It updates the goal and the agenda.
        :param sys_act: System action.
        :return:
        '''
        # Update previous goal.
        self.prev_goal = copy.deepcopy(self.goal)

        # Update the user patience level.
        if self.lastUserAct is not None and self.lastUserAct.act == 'repeat' and\
                        self.lastSysAct is not None and self.lastSysAct.act == 'repeat' and\
                        sys_act.act == 'repeat':
            # Endless cycle of repeating repeats: reduce patience to zero.
            self.goal.patience = 0

        elif sys_act.act == 'badact' or sys_act.act == 'null' or\
                (self.lastSysAct is not None and self.lastUserAct.act != 'repeat' and self.lastSysAct == sys_act):
            # Same action as last turn. Patience decreased.
            self.goal.patience -= 1

        if self.goal.patience < 1:
            logger.debug(str(self.goal))
            logger.debug('All patience gone. Clearing agenda.')
            self.hdcSim.agenda.clear()
            # Pushing bye act onto agenda.
            self.hdcSim.agenda.push(DiaAct.DiaAct('bye()'))
            return

        # Update last system action.
        self.lastSysAct = sys_act

        # Process the sys_act
        self.hdcSim.receive(sys_act, self.goal)

        # logger.warning('should update goal information')

    def respond(self):
        '''
        This method is called after receive() to get the user dialogue act response.
        The method first increments the turn counter, then pops n items off the agenda to form
        the response dialogue act. The agenda and goal are updated accordingly.

        :param None:
        :returns: (instance) of :class:`DiaAct` 
        '''
        user_output = self.hdcSim.respond(self.goal)

        if user_output.act == 'request' and len(user_output.items) > 0:
            # If there is a goal constraint on near, convert act type to confirm
            # TODO-  do we need to add more domain dependent type rules here for other domains beyond TT?
            # this whole section mainly seems to stem from having "area" and "near" in ontology... 
            if user_output.contains_slot('near') and self.goal.contains_slot_const('near'):
                for const in self.goal.constraints:
                    if const.slot == 'near':
                        near_const = const.val
                        near_op = const.op
                        break
                # original: bug. constraints is a list --- near_const = self.goal.constraints['near']
                if near_const != 'dontcare':
                    if near_op == "=":   # should be true for 'dontcare' value
                        #TODO - delete-WRONG-user_output.dact['act'] = 'confirm'
                        #TODO-delete-user_output.dact['slots'][0].val = near_const
                        user_output.act = 'confirm'
                        user_output.items[0].val = near_const
                    
        self.lastUserAct = user_output
        #self.goal.update_au(user_output)
        return user_output

#END OF FILE
