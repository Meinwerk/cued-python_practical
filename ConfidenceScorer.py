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
