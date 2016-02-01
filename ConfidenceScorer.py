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
ConfidenceScorer.py -
===================================================

Author: Dongho Kim  (Copyright CUED Dialogue Systems Group 2015)

.. seealso:: CUED Imports/Dependencies: 

    None


.. warning::

        Documentation not done

************************

''' 



class AdditiveConfidenceScorer():
    '''Additive confidence scoring of TODO
    '''
    def __init__(self, topProb1, rescale):
        self.rescale = rescale
        self.TOP_PROB_IS_ONE = topProb1
    
    def assignConfScores(self, dapl):
        '''
        @param dapl: N-best list of DiaAct
        '''
        outlist = []
        outdactlist = []
        total = 0.0
        for hyp in dapl:    # for each hyp in the given N-best list
            total += hyp.P_Au_O
            if hyp not in outdactlist: # Add this hyp
                outlist.append(hyp)
                outdactlist.append(hyp)
            else:                           # or add P_Au_O
                i = outdactlist.index(hyp)
                outlist[i].P_Au_O += hyp.P_Au_O
                
        # Rescale
        if total > 1 or self.rescale:
            for h in outdactlist:
                h.P_Au_O = float(h.P_Au_O) / total
        
        outlist.sort()
        if self.TOP_PROB_IS_ONE and outlist:
            outlist = [outlist[0]]
            outlist[0].P_Au_O = 1.0
        
        return outlist


#END OF FILE
