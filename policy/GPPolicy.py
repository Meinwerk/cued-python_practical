'''
GPPolicy.py - Gaussian Process policy 
============================================

Author: Milica Gasic  (Copyright CUED Dialogue Systems Group 2015)

   
**Relevant Config variables** [Default values]::

    [gppolicy]
    kernel = polysort
    thetafile = ''
    revertfile = ''
    replacefile = ''

.. seealso:: CUED Imports/Dependencies: 

    import :class:`GPLib` |.|
    import :class:`DMUtils` |.|
    import :class:`Settings` |.|
    import :class:`ContextLogger`

.. warning::
        Documentation not done.

************************

'''


__author__ = 'milicagasic'
import cStringIO, tokenize
import math
import copy

from GPLib import *
import DMUtils
import Settings
import DomainUtils
import ContextLogger
logger = ContextLogger.getLogger(__name__)


def countValues(b):
    n = 0
    for elem in b:
        n +=elem[1]
    return n


class GPAction():
    '''GP action
    Definition of summary action used for GP-Sarsa
    '''
    def __init__(self):
        self.numActions = 0
        self.act = ""


    def replaceAction(self, a, replace):
        '''
        Used for making abstraction of an action
        '''
        slot = a.split("_")[1]
        if slot in replace:
            replacement = replace[slot]

            return a.replace(slot, replacement)
        return a


    def __init__(self, action, n, replace={}):

        self.act=action
        if len(replace) > 0:
            self.act = self.replaceAction(a, replace)

        self.numActions = n

    def __eq__(self, a):
        """
        Action are the same if their strings match
        :rtype : bool
        """
        if self.numActions != a.numActions:
            return False
        if self.act != a.act:
                return False
        return True

    def __ne__(self, a):
        return not self.__eq__(a)

    def show(self):
        '''
        Prints out action and total number of actions
        '''
        print string(self.act), " ", string(self.numActions)


    def toString(self):
        '''
        Prints action
        '''
        return self.act




class GPState():
    '''GP State
    Definition of state needed for GP-Sarsa algorithm
    Main requirement the ability to compute kernel function over two states
    '''

    def __init__(self, belief, keep_none=False, replace={}, domainUtil=None):
        self.domainUtil =  domainUtil
        # get constants
        self._bstate = {}
        self.keep_none = keep_none
        #self.extractBelief(b, replace)
        self.extractSimpleBelief(belief,replace)

    def extractBeliefWithoutOther(self, belief):
        '''
        Produces a vector of [ [p_0, 1], ..., [p_n, 1] ] where p_0 to p_n are probability distributions
        '''
        res = []
        for value in belief.keys():
            elem = belief[value]

            res_elem = [elem, 1.0]
            res.append(res_elem)

        return res

    def extractBeliefWithOther(self, belief, other=0):
        '''
        Copies a belief vector, computes the remaining belief, appends it and returnes its sorted value
        '''
        res = []
        tmp = self.extractBeliefWithoutOther(belief)

        sum_prob = 0.0

        for elem in tmp:
            res.append(elem)
            sum_prob += elem[0] * elem[1]

        other -=len(tmp)

        if self.keep_none or other>0:
            none_prob = 1.0 - sum_prob
            elem = []
            elem.append(none_prob)
            elem.append(1 if other==0 else other)
            res.append(elem)

        res = sorted(res, key=lambda elem: elem[0], reverse=True)

        return res

    def extractSingleValue(self, val, name):
        '''
        for a probability p returns a vector [p, 1-p]
        '''
        tmp = {}
        res = []
        elem = []
        nelem = []
        elem.append(val)
        elem.append(1)
        tmp[name] = elem
        nelem.append( 1 - val)
        nelem.append(1)
        tmp["not" + name] = nelem

        for slot in tmp.keys():
            res.append(tmp[slot])

        return res

    def extractSimpleBelief(self, b, replace={}):
        '''
        From the belief state b extracts discourseAct, method, requested slots, name, goal for each slot,
        history whether the offer happened, whether last action was inform none, and history features
        '''
        with_other = 0
        without_other = 0

        self.isFullBelief = True


        for elem in b['beliefs'].keys():
            if elem == 'discourseAct':
                goalDiscourseAct = b['beliefs'][elem]
                self._bstate["goal_discourseAct"] = self.extractBeliefWithoutOther(copy.deepcopy(goalDiscourseAct))
                without_other +=1
            elif elem == 'method':
                goalMethod = b['beliefs'][elem]
                self._bstate["goal_method"] = self.extractBeliefWithoutOther(copy.deepcopy(goalMethod))
                without_other +=1
            elif elem == 'requested' :
                for slot in b['beliefs'][elem]:
                    cur_slot=slot
                    if len(replace) > 0:
                        cur_slot = replace[cur_slot]
                    self._bstate['hist_'+cur_slot] = self.extractSingleValue(
                                            copy.deepcopy(b['beliefs']['requested'][slot]),
                                            'requested')
                    without_other +=1
            else:
                if elem == 'name':

                    self._bstate[elem] = self.extractBeliefWithOther(
                                            copy.deepcopy(b['beliefs']['name']), 
                                            len(self.domainUtil.ontology['informable']['name'])+2)
                    with_other +=1
                else:
                    cur_slot=elem
                    if len(replace) > 0:
                        cur_slot = self.relace[elem]

                    self._bstate['goal_'+cur_slot] = self.extractBeliefWithOther(
                                                        copy.deepcopy(b['beliefs'][elem]),
                                                        len(self.domainUtil.ontology['informable'][elem])+2)
                    with_other += 1

                    n = countValues(self._bstate['goal_'+cur_slot])
                    if n!=len(self.domainUtil.ontology['informable'][elem])+2:
                        print self._bstate['goal_'+cur_slot]
                        logger.error("Different number of values for slot "+cur_slot+" "+str(n)+\
                                " in ontology "+ str(len(self.domainUtil.ontology['informable'][elem])+2) ) 
                    

        self._bstate["hist_offerHappened"] = self.extractSingleValue(
                                                1.0 if b['features']['offerHappened'] else 0.0,
                                                "offerHappened")
        without_other +=1
        self._bstate["hist_lastActionInformNone"] = self.extractSingleValue(
                                                        1.0 if len(b['features']['informedVenueSinceNone'])>0 else 0.0,
                                                        "lastActionInformNone")
        without_other +=1
        i=0
        for inform_elem in b['features']['inform_info']:
            self._bstate["hist_info_"+str(i)] = self.extractSingleValue(1.0 if inform_elem else 0.0, "info_"+str(i))
            i += 1
            without_other +=1

    def extractBelief(self, b, replace=[]):
        '''
        '''
        self.isFullBelief = True

        goal = b["goal"]
        goalSlotNames = b["slotAndName"]
        valueList = b["slotValueList"]
        goalName = b["name"]
        goalDiscourseAct = b["discourseAct"]
        goalMethod = b["method"]
        nameValueList = b["nameValueList"]
        goalHistory = b["goal_grounding"]
        infoHistory = b["info_grounding"]
        infoSlotNames = b["infoSlots"]
        informInfo = b["inform_info"]

        lastActionInformNone = b["lastActionInformNone"]
        offerHappened = b["offerHappened"]

        self._bstate["hist_lastActionInformNone"] = self.extractSingleValue(lastActionInformNone,
                                                                           "lastActionInformNone")
        self._bstate["hist_offerHappened"] = self.extractSingleValue(offerHappened, "offerHappened")

        for i in range(len(goal)):
            tmp = {}
            curSlotName = goalSlotNames[i]
            size = len(valueList)
            curProbs = goal[i]
            if len(replace) > 0:
                curSlotName = relace[curSlotName]

            curBelief = self.extractBeliefWithOther(curProbs)

            self._bstate["goal_" + curSlotName] = curBelief

        curBelief = self.extractBeliefWithOther(goalName)

        self._bstate["goal_name"] = curBelief

        self._bstate["goal_discourseAct"] = self.extractBeliefWithoutOther(goalDiscourseAct)

        self._bstate["goal_method"] = self.extractBeliefWithoutOther(goalMethod)

        for i in range(min(len(goalSlotNames), len(goalHistory))):
            histName = goalSlotNames[i]
            curHistProbs = goalHistory[i]
            curHistBelief = self.extractBeliefWithoutOther(curHistProbs)

            if len(replace) > 0:
                hisName = replace[histName]

            self._bstate["hist_" + histName] = curHistBelief

        for i in range(min(len(infoSlotNames), len(infoHistory))):
            infoName = infoSlotNames[i]

            if len(replace) > 0:
                infoName = replace[infoName]

            curInfoProbs = infoHistory[i]
            curInfoBelief = self.extractBeliefWithoutOther(curInfoProbs)

            self._bstate["hist_" + infoName] = curInfoBelief

        self.state_size = len(ns._bstate)


    def toString(self):
        '''
        String representation of the belief
        '''
        res = ""

        if len(ns._bstate) > 0:
            res += string(len(ns._bstate)) + " "
            for slot in ns._bstate:
                res += slot + " "
                for elem in ns._bstate[slot]:
                    for e in elem:
                        res += string(e) + " "

        return res


class Kernel():
    '''Kernel for GP
    '''
    def __init__(self, kernel_type, theta, der=-1, revert={}):
        '''
        self.kernel_type specifies the type of kernel
        self.theta are kernel parameters
        self.der is the derivative
        '''
        self.kernel_type = kernel_type
        self.theta = theta
        self.der = der
        self.revert = revert #not used at the moment


    def sigma(self):
        '''
        Noise parameter
        '''
        return theta[-1]

    def gaussSort(self, n, p, q):
        '''
        Euclidian distance for two elements which repeat themselves n times
        Used to compute Gauss kernel
        '''
        r = n * (p - q) * (p - q)
        return r

    def getSortedVectors(self, a, b, n, a_exact, b_exact):
        '''
        computes a, b, and n vector where n specifies how many times elements in a_exact and b_exact repeat
        '''
        index_a = 0
        index_b = 0
        na = a[0][1]
        nb = b[0][1]
        while index_a < len(a) and index_b < len(b):
            na = a[index_a][1]
            nb = b[index_b][1]
            nmin = min(na, nb)
            na -= nmin
            nb -= nmin
            a_exact.append(a[index_a][0])
            b_exact.append(b[index_b][0])
            n.append(nmin)
            if na == 0:
                index_a += 1
            if nb == 0:
                index_b += 1


    def dist(self, a, b, sorting):
        '''
        Compute kernel of two vectors a and b, optionally they can be sorted
        '''
        ker = 0.0
        n = []
        a_exact = []
        b_exact = []

        if sorting:
            self.getSortedVectors(copy.deepcopy(a), copy.deepcopy(b), n, a_exact, b_exact)

        elemsize = len(a)
        if sorting:
            elemsize = len(n)

        for i in range(elemsize):
            nval = 0
            aval = 0
            bval = 0

            if sorting:
                nval = n[i]
                aval = a_exact[i]
                bval = b_exact[i]
            else:
                nval = min(a[i][1], b[i][1])
                aval = a[i][0]
                bval = b[i][0]

            if nval > 0:
                if self.kernel_type == "polysort":
                    if sorting:
                        ker += nval * aval * bval *2.0;
                    else:
                        ker += nval * aval * bval/2.0;
                elif self.kernel_type == "gausssort":
                    ker += self.gaussSort(nval, aval, bval)

        return ker


    def subKernel(self, aslot, a, b):
        '''
        Kernel value for a particular slot
        '''
        sorting = False

        if "goal" in aslot and aslot != "goal_discourseAct" and aslot != "goal_method" :
            sorting = True

        ker = self.dist(a, b, sorting)

        if self.kernel_type == "gausssort":

            if len(self.theta)!=2:
                logger.warning("Parameters not given")
            p = self.theta[0]
            sigmak = self.theta[1]
            if p < 0 or sigmak < 0:
                return float('nan')
            elif self.der == -1:
                ker = p * p * math.exp(-ker / (1 * sigmak * sigmak))
            elif self.der == 0:
                ker = 2 * p * math.exp(-ker / (1 * sigmak * sigmak))
            elif self.der == 1:
                ker = p * p * math.exp(-ker / (1 * sigmak * sigmak)) * ker / pow(sigmak, 3)
            else:
                ker = 0

        return ker


    def node2RevertedNode(self, node, revert): #not used at the moment
        '''
        '''
        [prefix, slot]= node.split("_")
        revertedslots = []

        for elem in revert.keys():
            if revert[elem]==slot:
                return elem

    def coreKernel(self, ns, s):
        '''
        Kernel value between two GP states ns and s
        '''
        ker = 0.0;
        for islot in ns._bstate.keys():
            if islot == "hist_location":
                continue
            a = ns._bstate[islot]

            if islot in s._bstate:
                b = s._bstate[islot]

                if countValues(a)!=countValues(b):
                    if "_" in islot:
                        slot_name = islot.split("_")[1]
                    else:
                        slot_name = islot
                    print a
                    print b
                    logger.error("Corresponding parts of belief for slot "+islot+\
                            " have different sizes, a is "+str(countValues(a))+" and b is "+str(countValues(b)))

                ker += self.subKernel(islot, a, b)
            elif len(self.revert) > 0:

                revertednode = self.node2RevertedNode(islot, self.revert)
                if revertednode in s._bstate:
                    b = s._bstate[revertedlist[i]]
                    ker += self.subKernel(islot, a, b)


        if type == "polysort":
            if der == -1:
                ker *= cnts.p
            elif der == 0:
                ker *= 1;
            else:
                ker = 0;

        return ker

    def revertAction(self, na, a):
        '''
        '''
        if "_" in na and len(na.split("_")==2):

            [prefix, slot] = na.split("_")
            if slot in self.revert:
                reverted_act = prefix + self.revert[slot][0]
                if reverted_act == a:
                    return 1.0
        return 0.0;


    def ActionKernel(self, na, a):
        '''
        Kroneker delta on actions
        '''
        if len(self.revert) > 0:
            if self.revertAction(na, a) > 0.0:
                return 1.0
        if na.act == a.act:
            return 1.0

        return 0.0

    def Kernel(self, ns, s):
        '''
        Final kernel value
        '''
        ker = self.coreKernel(ns, s)

        return ker

    def PriorKernel(self, ns, s):
        '''
        Prior Kernel is normalised
        '''
        core =  self.coreKernel(ns, s)
        nskernel =  self.coreKernel(ns, ns)
        skernel = self.coreKernel(s, s)

        return core/math.sqrt(nskernel*skernel)

class GPPolicy():
    '''
    Gaussian process policy uses GPSarsa algorithm to opmise actions where states are GPState and actons are GPActoin
    '''
    def __init__(self, inpolicyfile, outpolicyfile, numA, actionNames, domainUtil, learning):  

        self.domainUtil = domainUtil
        self.learning = learning
        self.actionNames = actionNames
        self.numActions = numA
        self.kerneltype = "polysort"
        self.thetafile = ""
        self.theta = [1.0, 1.0]
        self.revertfile = ""
        self.revert = {}
        self.replacefile = ""
        self.replace ={}

        #get config variables
        configs = []
        if Settings.config.has_option("gppolicy_"+domainUtil.domainString, "kernel"):
            configs.append('kernel')
            self.kerneltype = Settings.config.get("gppolicy_"+domainUtil.domainString, "kernel")
        if Settings.config.has_option("gppolicy_"+domainUtil.domainString, "thetafile"):
            configs.append('thetafile')
            self.thetafile = Settings.config.get("gppolicy_"+domainUtil.domainString, "thetafile")
        if Settings.config.has_option("gppolicy_"+domainUtil.domainString, "revertfile"):
            configs.append('revertfile')
            self.revertfile = Settings.config.get("gppolicy_"+domainUtil.domainString, "revertfile")
        if Settings.config.has_option("gppolicy_"+domainUtil.domainString, "replacefile"):
            configs.append('replacefile')
            self.replacefile = Settings.config.get("gppolicy_"+domainUtil.domainString, "replacefile")

        # Learning algorithm:
        self.learner = GPSARSA(inpolicyfile,outpolicyfile,domainString=domainUtil.domainString, learning=self.learning)

        self.ReadTheta()

        self.ReadFile(self.replacefile, self.replace)
        self.ReadFile(self.revertfile, self.revert)

        self.strace = []
        self.atrace = []
        self.rtrace = []
        self.totalreward = 0
        self.kernel = Kernel(self.kerneltype, self.theta, -1, self.revert)
        self._byeAction = -1

        for i in range(len(self.actionNames)):
            if "bye" in self.actionNames[i]:
                self._byeAction=i


    def ReadTheta(self):
        '''
        Kernel parameters
        '''
        if self.thetafile != "":
            f = open(self.thetafile, 'r')
            for line in f:
                line = line.strip()
                elems =line.split(" ")
                for elem in elems:
                    self.theta.append(float(elem))
                break
            f.close()

    def ReadFile(self, fname, store):
        '''
        Reads replace and revert abstactions for slots
        '''
        if fname != "":
            f = open(fname, r)
            for line in f:
                line = line.strip()
                elems = line.split(" ")
                assert(len(elems) == 2)
                store[elems[0]]=elems[1]
            f.close()

    def startLearningEpisode(self):
        '''
        Function called at the beginning of learning
        '''
        self.learner.learning = True;
        self.strace = []
        self.atrace = []
        self.rtrace = []
        self.totalreward = 0 


    def endLearningEpisode(self):
        '''
        At the end of learning episode calls LearningStep for accumulated states and actions and rewards
        '''
        if len(self.strace) == 0:
            return
        if not self.learner.learning:
            logger.warning("Policy not learning")
            return


        assert(len(self.strace)==len(self.atrace))
        i=1
        r=0
        while i< len(self.strace) and self.learner.learning:

            if i ==1:
                self.learner.initial = True
                self.learner.terminal = False
            elif i+1 == len(self.strace):
                self.learner.initial = False
                self.learner.terminal = True
            else:
                self.learner.initial = False
                self.learner.terminal = False
            if i+1 == len(self.strace):
                r = self.totalreward

            self.learner.LearningStep( self.strace[i-1], self.atrace[i-1], r , self.strace[i], self.atrace[i], self.kernel)
            i+=1


    def CreateExecutable(self,nonExecutableActions):
        '''
        Produce a list of executable actions from non executable actions
        '''
        final = []

        for i in range(len(self.actionNames)):
            if self.actionNames[i] in nonExecutableActions:
                continue
            else:
                action = GPAction(self.actionNames[i],self.numActions, self.replace)
                final.append(action)

        return final


    def MatchingActions(self, act):
        '''
        Matching actions
        '''
        assert(len(act.split("_"))==2)
        [prefix, slot] = act.split("_")

        matchingactions = []

        for elem in self.replace.keys():
            if replace[elem] == slot:
                match=prefix+elem
                matchingactions.append(match)
        return matchingactions

    def ActionString(self, act):
        '''
        Produce a string representation from an action
        '''
        if len(self.replace) == 0 and len(self.revert) == 0:
            for i in range(len(self.actionNames)):
                if self.actionNames[i] == act:
                    return self.actionNames[i]
        else:
            matchingactions = MatchingActions(act)
            for i in range(self.actionNames):
                for j in range(matchingactions):
                    if self.actionNames[i]==matchingactions[j]:
                        return self.actionNames[i]

        assert(0)


    def nextAction(self, belief, nonExectuableActions):
        '''
        Selects next action to take based on the current belief and a list of non executable actions
        '''
        goalMethod = belief["beliefs"]["method"]
        if "finished" in goalMethod:
            finishedprob = goalMethod["finished"]
        if finishedprob > 0.85 and self._byeAction != -1:
            return self._byeAction

        assert(len(self.replace)==0)
        currentstate = GPState(belief, replace=self.replace, domainUtil=self.domainUtil)


        if self._byeAction != -1:
            nonExectuableActions.append(self._byeAction)

        executable = self.CreateExecutable(nonExectuableActions)

        if len(executable) < 1:
            logger.error("No executable actions")

        nbest = self.learner.policy(currentstate, self.kernel, executable)

        ans = self.ActionString(nbest[0].act)

        return ans


    def getPriorVar(self, belief, act):
        '''
        Returns prior variance for a given belief and action
        '''
        action = GPAction(act, self.numActions, self.replace)
        state = GPState(belief,replace=self.replace, domainUtil=self.domainUtil)
        return self.learner.getPriorVar(state, action, self.kernel)

    def getValues(self, belief, nonExecutableActions):
        '''
        :returns: list of Q-values and likelihoods for each executable element
        '''
        executable = []
        goalMethod = belief["method"]
        if "finished" in goalMethod:
            finishedprob = goalMethod["finished"]
        if finishedprob > 0.85 and self._byeAction != -1:
            return self._byeAction

        currentstate = GPState(belief, replace=self.replace, domainUtil=self.domainUtil)

        if self._byeAction != -1:
            nonExecutableActions.append(self._byeAction)

        if len(executable) == 0:

            nonExecutableActions.append(self._byeAction)
            executable = self.CreateExecutable(nonExecutableActions)

        values = []

        for i in len(executable):

            [value, likelihood] = self.learner.getValue(currentstate, self.kernel, executable[i])
            values.append([self.ActionString(executable[i].act),value,likelihood])

        return values

    def recordExecutedAction(self, belief, act, reward):
        '''
        For current belief and executed action record the belief
        '''
        currentstate = GPState(belief, replace=self.replace, domainUtil=self.domainUtil)
        currentaction = GPAction(act, self.numActions, self.replace)
        self.totalreward += reward
        self.strace.append(currentstate)
        self.atrace.append(currentaction)
        self.rtrace.append(reward)

    def getPolicyName(self):
        '''
        Returns the policy file name
        '''
        return self.policy_file

    def savePolicy(self):
        '''
        Saves the GP policy
        '''
        self.learner.savePolicy()


#END OF FILE
