#########################################################
# CUED Python Statistical Spoken Dialogue System Software
#########################################################
#
# Copyright 2015-16  Cambridge University Engineering Department 
# Dialogue Systems Group
#
# Principal Authors:  Dongho Kim and David Vandyke, Pei-Hao (Eddy) Su
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
GPLib.py - Gaussian Process policy tools
============================================

Author: Milica Gasic, Pei-Hao (Eddy) Su (Copyright CUED Dialogue Systems Group 2015)

   
**Relevant Config variables** [Default values].  X is the domain tag::

    [gpsarsa_X]
    saveasprior = False 
    random = False
    learning = False
    gamma = 1.0
    sigma = 5.0
    nu = 0.001
    scale = -1
    numprior = 0

.. seealso:: CUED Imports/Dependencies: 

    import :class:`Settings` |.|
    import :class:`ContextLogger`

.. warning::
        Documentation not done.

************************

'''

__author__ = 'milicagasic'

import numpy as np
import math
import scipy.stats
import pickle as pkl
import os.path
import random

import Settings
import ContextLogger
logger = ContextLogger.getLogger('')

class LearnerInterface:
    '''GP policy utility class.
    specifies the policy files
    self._inputDictFile input dictionary file
    self._inputParamFile input parameter file
    self._outputDictFile output dictionary file
    self._outputParamFile output parameter file

    self.initial self.terminal flags are needed for learning to specify initial and terminal states in the episode
    '''
    def __init__(self):

        self._inputDictFile = ""
        self._inputParamFile = ""
        self._outputDictFile = ""
        self._outputParamFile = ""
        self._actionSize = 0
        self.initial = False
        self.terminal = False

    def DictionarySize(self):
        return 0
    def savePolicy(self, index):
        pass

    def readPolicy(self):
        pass

    def getValue(self, state, action):
        return [0, 0]

    def policy(self, state, kernel=None, executable = []):
        pass

    def LearningStep(self, pstate, paction, r, state, action, kernel):
        pass

class GPSARSAPrior(LearnerInterface):
    '''Derives from LearnerInterface.
    '''
    def __init__(self,in_policyfile, out_policyfile, numPrior=-1):
        self._inpolicyfile = in_policyfile
        self._outpolicyfile = out_policyfile

        self._actionSize = 0
        self.initial = False
        self.terminal = False
        self._dictionary = []
        self._alpha_tilda = []
        self._inputDictFile =""
        self._inputParamFile = ""
        self._outputDictFile = ""
        self._outputParamFile = ""
        self._prior = None
        self._superior = None
        
        if numPrior >= 0:
            if numPrior > 0:
                self._prior = GPSARSAPrior(in_policyfile,out_policyfile ,numPrior-1)
                self._prior._superior = self

            else:
                self._prior = None
            
            self._inputDictFile = in_policyfile+"."+str(numPrior)+".prior.dct"
            self._inputParamFile = in_policyfile+"."+str(numPrior)+".prior.prm"
            self._outputDictFile = out_policyfile+"."+str(numPrior)+".prior.dct"
            self._outputParamFile = out_policyfile+"."+str(numPrior)+".prior.prm"
            self.readPolicy()


    def readParameters(self):
        """
        Reads input policy parameters
        """
        pkl_file = open(self._inputParamFile, 'rb')
        self._alpha_tilda = pkl.load(pkl_file)
        pkl_file.close()

    def readDictionary(self):
        """
        Reads input policy dictionary file
        """
        pkl_file = open(self._inputDictFile, 'rb')
        self._dictionary = pkl.load(pkl_file)
        logger.info("Read dictionary of size "+str(len(self._dictionary)))   
        pkl_file.close()

    def DictionarySize(self):
        """
        :returns: number of dictionary points
        """
        return len(self._dictionary)

    def SavePolicy(self, index):
        """
        This function does not exist for prior only for full GP
        """
        pass

    def readPolicy(self):
        """
        Reads dictionary file and parameter file
        """
        if not os.path.isfile(self._inputDictFile) or not os.path.isfile(self._inputParamFile):
            if self.learning or self._random:
                logger.warning(self._inpolicyfile+" does not exist")
                return
            else:
                logger.error(self._inpolicyfile+" does not exist")
        self.readDictionary()
        self.readParameters()

    def QvalueMean(self, state, action, kernel):
        """
        :returns: Q value mean for a given state, action and the kernel function
        Recursively calculates the mean given depending on the number of recursive priors
        """
        if self._prior != None :
            qprior = self._prior.QvalueMean()
        else:
            qprior = 0

        if len(self._dictionary)>0:
            k_tilda_t =self.k_tilda(state, action, kernel)
            qval = np.dot(self._alpha_tilda,k_tilda_t)
            mean = qprior+qval
        else:
            mean = qprior

        return mean


    def k_tilda(self,state, action, kernel):
        """
        :returns: vector of kernel values of given state, action and kernel with all state-action pairs in the dictionary
        """
        res = []
        for [dstate, daction] in self._dictionary:

            actKer = kernel.ActionKernel(action, daction)
            if actKer > 0:
                if self._prior != None:
                    stateKer = kernel.Kernel(state, dstate)
                elif self._superior != None and self._prior == None:
                    stateKer = kernel.PriorKernel(state, dstate)
                else:
                    stateKer = kernel.Kernel(state, dstate)
                res.append(actKer*stateKer)
            else:
                res.append(actKer)

        return np.array(res)


class GPSARSA(GPSARSAPrior):
    """Derives from GPSARSAPrior
       Implements GPSarsa algorithm where mean can have a predefined value
       self._num_prior specifies number of means
       self._prior specifies the prior
       If not specified a zero-mean is assumed

       Parameters needed to estimate the GP posterior
       self._K_tida_inv inverse of the Gram matrix of dictionary state-action pairs
       self._C_tilda covariance function needed to estimate the final variance of the posterior
       self._c_tilda vector needed to calculate self._C_tilda
       self._alpha_tilda vector needed to estimate the mean of the posterior
       self._d and self._s sufficient statistics needed for the iterative estimation of the posterior

       Parameters needed for the policy selection
       self._random random policy choice
       self._scale scaling of the standard deviation when sampling Q-value, if -1 than taking the mean
       self.learning if true in learning mode
    """
    def __init__(self, in_policyfile, out_policyfile, domainString=None, learning=False):
        """
        Initialise the prior given policy files
        """
        GPSARSAPrior.__init__(self,in_policyfile,out_policyfile,-1)

        self.save_as_prior = False
        self.initial = False
        self.terminal = False
        self._gamma = 1.0
        self._sigma = 5.0
        self._nu = 0.001

        self._K_tilda_inv = np.array([])
        self._C_tilda = np.array([])
        self._c_tilda = np.array([])
        self._a = np.array([])
        self._alpha_tilda = np.array([])
        self._dictionary = []
        self._d = 0
        self._s = float('inf')

        self._random = False
        self._num_prior = 0
        self._scale = -1
        self._prior = None
        self.learning = learning

        configs = [] 
        if Settings.config.has_option("gpsarsa_"+domainString, "saveasprior"):
            configs.append('saveasprior')
            self.save_as_prior = Settings.config.getboolean("gpsarsa_"+domainString, "saveasprior")
        if Settings.config.has_option("gpsarsa_"+domainString, "numprior"):
            configs.append('numprior')
            self._num_prior = Settings.config.getint("gpsarsa_"+domainString,"numprior")  
        if Settings.config.has_option("gpsarsa", "random"):
            configs.append('random')
            self._random = Settings.config.getboolean("gpsarsa_"+domainString, "random")
        if Settings.config.has_option("gpsarsa_"+domainString, "gamma"):
            configs.append('gamma')
            self._gamma = Settings.config.getfloat("gpsarsa_"+domainString,"gamma")
        if Settings.config.has_option("gpsarsa_"+domainString, "sigma"):
            configs.append('sigma')
            self._sigma = Settings.config.getfloat("gpsarsa_"+domainString,"sigma")
        if Settings.config.has_option("gpsarsa_"+domainString, "nu"):
            configs.append('nu')
            self._nu = Settings.config.getfloat("gpsarsa_"+domainString,"nu")
        if Settings.config.has_option("gpsarsa_"+domainString, "scale"):
            configs.append('scale')
            self._scale = Settings.config.getint("gpsarsa_"+domainString,"scale")


        if self._num_prior == 0 and self._inputDictFile == "" and self._outputDictFile == "" :
            self._inputDictFile = in_policyfile+".dct"
            self._inputParamFile = in_policyfile + ".prm"
            self._outputDictFile = out_policyfile + ".dct"
            self._outputParamFile = out_policyfile + ".prm"
        else:
            self._inputDictFile = in_policyfile+".dct"
            self._inputParamFile = in_policyfile + ".prm"
            self._outputDictFile = out_policyfile + ".dct"
            self._outputParamFile = out_policyfile + ".prm"

        # load the parameters using self._input<X>
        self.readPolicy()

        if self._num_prior > 0:
            self._prior = GPSARSAPrior(out_policyfile,'' ,self._num_prior-1)
            self._prior._superior = self

    def ReInitialise(self):
        """
        :param: None
        :returns None:
        """
        if len(self._ditionary) > 0:
            self._K_tilda_inv = np.array([])
            self._C_tilda = np.array([])
            self._c_tilda = np.array([])
            self._a = np.array([])
            self._alpha_tilda = np.array([])
            self._dictionary = []
            self._d = 0
            self._s = float('inf')

        self.initial = True
        self.terminal = False

    def Reset(self):
        """
        Resets to new dialogue
        """
        self.initial = True
        self.terminal = False

    def QvalueMeanVar(self, state, action, kernel):
        """
        :returns: mean and variance of GP for given state, action and kernel
        """
        qprior = 0
        qval = 0
        qvar = 0

        if self._prior != None:
            qprior = self._prior.QvalueMean(state, action, kernel)

        if len(self._dictionary) > 0 :
            k_tilda_t = self.k_tilda(state,action,kernel)
            qval = np.dot(k_tilda_t,self._alpha_tilda)
            qvar = np.dot(k_tilda_t,np.dot(self._C_tilda,k_tilda_t))

        mean = qprior + qval
        qorg = kernel.Kernel(state,state)*kernel.ActionKernel(action,action)
        var = qorg - qvar

        if var < 0:
            logger.error("Variance negative "+str(var))
            var =0

        return [mean, var]


    def getPriorVar(self, state, action, kernel):
        """
        :returns: prior variance for given state, action and kernel
        """
        priorVar = kernel.Kernel(state,state)*kernel.ActionKernel(action,action)
        return (self._scale**2)*priorVar

    def getValue(self, state, action, kernel):
        """
        :returns: mean of GP for given state, action and kernel function
        also samples a value form GP and returns likelihood of that value
        """
        likelihood = 1
        [mean, variance] = self.QvalueMeanVar(state, action, kernel)
        gaussvar = self._scale * math.sqrt(variance)

        if gaussvar > 0:
            value = gaussvar * np.random.randn() + mean
            likelihood = scipy.stats.norm(mean, gaussvar).pdf(value)

        return [ mean , likelihood ]

    def policy(self, state, kernel, executable=[]):
        """
        :returns: an ordered list of executable actions according to their Q estimates
        """
        if len(executable)==0:
            logger.error("No executable actions")
        random.shuffle(executable)

        if self._random:
            return executable

        Q =[]
        for action in executable:
            mean =0
            var =0
            if self._scale <= 0:
                mean = self.QvalueMean(state, action, kernel)
            else:
                [mean, var ] = self.QvalueMeanVar(state, action, kernel)
            value = mean
            if self._scale > 0:
                gaussvar = self._scale * math.sqrt(var)
                if gaussvar < 0:
                    logger.error("Negative variance")
                value = gaussvar * np.random.randn() + mean
            Q.append((action, value))

        Q=sorted(Q,key=lambda Qvalue : Qvalue[1], reverse=True)
        return [t[0] for t in Q]


    def Extend(self,delta_prev, pstate, paction):
        """
        Add points pstate and paction in the dictionary and extend sufficient statistics matrices and vectors for one dimension
        Only used for the first state action pair in the episode
        """
        _a_prev = np.zeros(len(self._dictionary)+1)
        _a_prev[-1] =1.0
        _c_tilda_prev = np.zeros(len(self._dictionary)+1)
        _K_tilda_inv_prev = self.extendKtildainv(self._K_tilda_inv,self._a,delta_prev)
        _alpha_tilda_prev = self.extendVector(self._alpha_tilda)
        _C_tilda_prev = self.extendMatrix(self._C_tilda)

        self._a = _a_prev
        self._alpha_tilda = _alpha_tilda_prev
        self._c_tilda = _c_tilda_prev
        self._C_tilda = _C_tilda_prev
        self._K_tilda_inv = _K_tilda_inv_prev

        self._dictionary.append([pstate,paction])
        #self.checkKtildainv(kernel)


    def extendMatrix(self, M):
        """
        Extend the dimentionality of matrix by one element
        """
        M_new = np.zeros((len(M[0])+1, len(M[0])+1))
        for i in range(len(M[0])):
            for j in range(len(M[0])):
                M_new[i][j]=M[i][j]
        return M_new

    def extendVector(self, v):
        """
        Extend the dimensionality of vector by one element
        """
        v_new = np.zeros(len(v)+1)
        for i in range(len(v)):
            v_new[i] = v[i]
        return v_new

    def extendKtildainv(self, K_tilda_inv, a, delta_new):
        """
        :returns: inverse of the Gram matrix using the previous Gram matrix and partition inverse theorem
        """
        K_tilda_inv_new = np.zeros((len(self._dictionary)+1,len(self._dictionary)+1))

        for i in range(len(self._dictionary)):
            for j in range(len(self._dictionary)):
                K_tilda_inv_new[i][j]=K_tilda_inv[i][j]+a[i]*a[j]/delta_new

            K_tilda_inv_new[i][-1]=-a[i]/delta_new
            K_tilda_inv_new[-1][i]=-a[i]/delta_new
        K_tilda_inv_new[-1][-1]=1/delta_new

        return K_tilda_inv_new


    def ExtendNew(self, delta_new, state, action, kernel, _a_new, k_tilda_prev, k_tilda_new, delta_k_tilda_new):
        """
        Add new state and action to the dictionary and extend sufficient statistics matrices and vectors for one dimension
        and reestimates all parameters apart form the ones involving the reward
        """
        _K_tilda_inv_new = self.extendKtildainv(self._K_tilda_inv, _a_new, delta_new)
        _a_new = np.zeros(len(self._dictionary)+1)
        _a_new[-1] =1.0
        _h_tilda_new = self.extendVector(self._a)
        _h_tilda_new[-1] = - self._gamma

        delta_k_new = np.dot(self._a,(k_tilda_prev-2.0*self._gamma*k_tilda_new)) \
                + (self._gamma**2)*kernel.Kernel(state,state)*kernel.ActionKernel(action,action)

        part1 = np.dot(self._C_tilda, delta_k_tilda_new)
        part2 = np.zeros(len(self._dictionary))\
                    if self.initial else (((self._gamma * (self._sigma ** 2)) * self._c_tilda)/self._s)

        _c_tilda_new = self.extendVector(_h_tilda_new[:-1] - part1  + part2)
        _c_tilda_new[-1] = _h_tilda_new[-1]

        spart1 = (1.0 + (self._gamma ** 2))* (self._sigma **2)
        spart2 = np.dot(delta_k_tilda_new,np.dot(self._C_tilda,delta_k_tilda_new))
        spart3 = 0.0  if self.initial else  ((2*np.dot(self._c_tilda, delta_k_tilda_new)\
                        - self._gamma*(self._sigma**2))*(self._gamma * (self._sigma ** 2 ))/self._s)

        _s_new = spart1 + delta_k_new - spart2 + spart3
        _alpha_tilda_new=self.extendVector(self._alpha_tilda)
        _C_tilda_new = self.extendMatrix(self._C_tilda)

        self._s = _s_new
        self._alpha_tilda = _alpha_tilda_new
        self._c_tilda = _c_tilda_new
        self._C_tilda = _C_tilda_new
        self._K_tilda_inv = _K_tilda_inv_new
        self._a = _a_new
        self._dictionary.append([state,action])
        #self.checkKtildainv(kernel)

    def NoExtend(self, _a_new, delta_k_tilda_new):
        """
        Resestimates sufficient statistics without extending the dictionary
        """
        _h_tilda_new = self._a - self._gamma * _a_new

        part1 = np.zeros(len(self._dictionary)) \
                    if self.initial else (self._c_tilda * (self._gamma * (self._sigma ** 2)) / self._s)
        part2 = np.dot(self._C_tilda,delta_k_tilda_new)
        _c_tilda_new = part1  + _h_tilda_new - part2

        spart1 = (1.0 + ( 0.0  if self.terminal else (self._gamma ** 2)))* (self._sigma **2)
        spart2 = np.dot(delta_k_tilda_new, (_c_tilda_new + (np.zeros(len(self._dictionary)) \
                        if self.initial else (self._c_tilda*(self._gamma) * (self._sigma ** 2)/self._s) ) ))
        spart3 = (0 if self.initial else ((self._gamma**2) * (self._sigma ** 4)/self._s) )

        _s_new = spart1  + spart2 - spart3
        self._c_tilda = _c_tilda_new
        self._s = _s_new
        self._a = _a_new


    def LearningStep(self, pstate, paction, reward, state, action, kernel):
        """
        The main function of the GPSarsa algorithm
        :parameter:
        pstate previous state
        paction previous action
        reward current reward
        state next state
        action next action
        kernel the kernel function

        Computes sufficient statistics needed to estimate the posterior of the mean and the covariance of the Gaussian process

        If the estimate of mean can take into account prior if specified
        """
        if self._prior != None:
            if not self.terminal:
                offset = self._prior.QvalueMean(pstate,paction,kernel) \
                        - self._gamma*self._prior.QvalueMean(state,action,kernel)
            else:
                offset = self._prior.QvalueMean(pstate,paction,kernel)

            reward = reward - offset

        if len(self._dictionary) == 0:
            self._K_tilda_inv = np.zeros((1,1))
            self._K_tilda_inv[0][0] = 1.0/(kernel.Kernel(pstate,pstate)*kernel.ActionKernel(paction,paction))

            self._a = np.zeros(1)+1.0
            self._alpha_tilda = np.zeros(1)
            self._C_tilda = np.zeros((1,1))
            self._c_tilda = np.zeros(1)
            self._d = 0.0
            self._s = float('inf')
            self._dictionary.append([pstate,paction])

        elif self.initial :
            k_tilda_prev = self.k_tilda(pstate,paction,kernel)
            self._a = np.dot(self._K_tilda_inv,k_tilda_prev)
            self._c_tilda = np.zeros(len(self._dictionary))
            delta_prev = kernel.Kernel(pstate,pstate)*kernel.ActionKernel(paction,paction) - np.dot(k_tilda_prev,self._a)
            self._d = 0.0
            self._s = float('inf')

            if delta_prev > self._nu :
                self.Extend(delta_prev, pstate, paction)

 
        k_tilda_prev = self.k_tilda(pstate,paction,kernel)
        
        
        #####################################################################
        # TODO:                                                             #
        # Complete the following sparcification criterion check             #
        # Follow the description of the GP-SARSA in the practical note.     #
        #####################################################################

        # HINT: use functions self.k_tilda for current k_tilda
        #           class kernel.Kernel and kernel.ActionKernel for current_kernel calculation

        # your code here...
        
        k_tilda_new = self.k_tilda(state, action, kernel)

        g_new = []
        if self.terminal:
            g_new = np.zeros(len(self._dictionary))
        else:
            # your code here...
            pass
            g_new = np.dot(self._K_tilda_inv,self.k_tilda)

        # your code here... modify current_kernel and estimate_kernel
        current_kernel = kernel.Kernel(pstate,pstate)*kernel.ActionKernel(paction,paction)    # simply the product of kernel.Kernel and kernel.ActionKernel
        estimate_kernel = np.dot(self.k_tilda, g_new)
        delta_new = 0.0 if self.terminal else (current_kernel - estimate_kernel)

        ## END TODO ##
       
        _a_new = g_new


        delta_k_tilda_new = k_tilda_prev -(np.zeros(len(self._dictionary)) if self.terminal else (self._gamma*k_tilda_new))

        _d_new = reward + (0.0 if self.initial else (self._gamma * (self._sigma ** 2)*self._d)/self._s ) \
                    - np.dot(delta_k_tilda_new,self._alpha_tilda)

        self._d =_d_new

        if delta_new<0 and math.fabs(delta_new)>0.0001:
            # just dont add this point to dictionary
            logger.warning("Negative sparcification "+str(delta_new))

        if delta_new > self._nu :
            self.ExtendNew(delta_new, state, action, kernel, _a_new, k_tilda_prev, k_tilda_new, delta_k_tilda_new)
        else:
            self.NoExtend(_a_new, delta_k_tilda_new)

        part1 = self._d/self._s
        self._alpha_tilda += self._c_tilda * part1
        if self.terminal:
            dummy = 1
        for i in range(len(self._dictionary)):
            for j in range(len(self._dictionary)):
                self._C_tilda[i][j] += self._c_tilda[i]*self._c_tilda[j]/self._s


    def checkKtildainv(self, kernel):
        """
        Checks positive definiteness
        :param: (instance) 
        """
        if not np.all(np.linalg.eigvals(self._K_tilda_inv) > 0):
            logger.error("Matrix not positive definite")

        K_tilda = []

        for [state, action] in self._dictionary:
            K_tilda.append(self.k_tilda(state,action,kernel))

        I = np.dot(np.array(K_tilda),self._K_tilda_inv)

        print np.array(K_tilda)
        for i in range(len(self._dictionary)):
            if math.fabs(I[i][i]-1.0)>0.0001:
                print I[i][i]
                logger.error("Inverse not calculated properly")
            for j in range(len(self._dictionary)):
                if i!=j and math.fabs(I[i][j])>0.0001:
                    print I[i][j]
                    logger.error("Inverse not calculated properly")

    def readPolicy(self):
        """
        Reads dictionary and parameter file
        """
        if not os.path.isfile(self._inputDictFile) or not os.path.isfile(self._inputParamFile):
            if self.learning or self._random:
                logger.warning(self._inpolicyfile+" does not exist")
                return
            else:
                logger.error(self._inpolicyfile+" does not exist and policy is not learning nor set to random")
        self.readDictionary()
        self.readParameters()

    def readDictionary(self):
        """
        Reads dictionary
        """
        if self._inputDictFile not in  ["",".dct"]:
            pkl_file = open(self._inputDictFile,'rb')
            self._dictionary = pkl.load(pkl_file)
            logger.warning("Read dictionary of size "+str(len(self._dictionary)))
            pkl_file.close()
        else:
            logger.warning("Dictionary file not given")

    def readParameters(self):
        """
        Reads parameter file
        """
        pkl_file = open(self._inputParamFile,'rb')
        # ORDER MUST BE THE SAME HERE AS WRITTEN IN saveParameters() below.
        self._K_tilda_inv = pkl.load(pkl_file)
        self._C_tilda = pkl.load(pkl_file)
        self._c_tilda = pkl.load(pkl_file)
        self._a = pkl.load(pkl_file)
        self._alpha_tilda = pkl.load(pkl_file)
        self._d = pkl.load(pkl_file)
        self._s = pkl.load(pkl_file)
        #-------------------------------
        pkl_file.close()

    def saveDictionary(self):
        """
        Saves dictionary
        :param None:
        :returns None:
        """
        pkl_file = open(self._outputDictFile,'wb')
        pkl.dump(self._dictionary,pkl_file)
        pkl_file.close()


    def saveParameters(self):
        """
        Save parameter file
        """
        pkl_file = open(self._outputParamFile,'wb') 
        # ORDER MUST BE THE SAME HERE AS IN readParameters() above.
        pkl.dump(self._K_tilda_inv,pkl_file)
        pkl.dump(self._C_tilda,pkl_file)
        pkl.dump(self._c_tilda,pkl_file)
        pkl.dump(self._a,pkl_file)
        pkl.dump(self._alpha_tilda,pkl_file)
        pkl.dump(self._d,pkl_file)
        pkl.dump(self._s,pkl_file)
        #-------------------------------
        pkl_file.close()


    def savePrior(self, priordictfile, priorparamfile):
        """
        Saves the current GP as a prior (these are only the parameters needed to estimate the mean)
        """
        pkl_file = open(priordictfile, 'wb')
        pkl.dump(self._dictionary, pkl_file)
        pkl_file.close()
        pkl_file = open(priorparamfile, 'wb')
        pkl.dump(self._alpha_tilda, pkl_file)
        pkl_file.close()

    def savePolicy(self):
        """Saves the GP dictionary (.dct) and parameters (.prm). Saves as a prior if self.save_as_prior is True.

        :param None:
        :returns: None
        """
        if self.save_as_prior :
            logger.info("saving GP policy: "+self._outpolicyfile + " as a prior")
            priordictfile = self._outpolicyfile +"."+ str(self._num_prior)+".prior.dct"
            priorparamfile = self._outpolicyfile +"."+ str(self._num_prior)+".prior.prm"
            self.savePrior(priordictfile,priorparamfile)
        else :
            logger.info("saving GP policy: "+self._outpolicyfile)
            self.saveDictionary()
            self.saveParameters()


#END OF FILE
