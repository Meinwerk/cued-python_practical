"""
RegexSemI.py - Regular expressions SemI parser base class
==========================================================

assumptions:
    - obs can be a ASR n-best list - potential sentence inputs each with a probability
        Currently - no probabilitiess - will have to slightly ammend code to deal with these.
    - will only output text semantic acts (plus probs maybe) -- wont be instances of DiaAct for example
    - go over act definintions - speak with Steve?. -- part of this is affirm()? confirm()?
    - "i dont want X" --> inform(slot!=X)   do we do this?

"""
import re,os
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.sys.path.insert(0,parentdir) 
import ContextLogger
logger = ContextLogger.getLogger('')


class RegexParser():
    """Is a  base class for each domains Regular Expressions based semantic parser. Primary focus is on **users intent**.
        The derived semantic parsers of each domain can deal with the constraints (slots,values).
    """
    def __init__(self, repoIn=None):
        self.init_regular_expressions()
        self.repoRoot=repoIn  # used when runing with FileParser() -- since without a config, root may be unavailable.

    def decode(self, obs):
        """Assumes input is either a single string or a list of tuples (string, prob) as in a nbest list.
        """ 
        # bundle up into a list if a single sentence (ie string) is input
        if isinstance(obs,str):
            obs = [obs]
        if not isinstance(obs,list):
            logger.error("Expecting a list or string as input") 
       
        all_hyps = []
        for ob in obs:
            if isinstance(ob,tuple):
                sentence,sentence_prob = ob[0],ob[1]
            elif isinstance(ob,str):
                sentence,sentence_prob = ob, None
            else:
                logger.error("For decoding, expected either a str or (str,probability) tuple") 
            assert(isinstance(sentence,str))
            all_hyps.append((self.decode_single_hypothesis(sentence),sentence_prob)) 
        return self.combine_parses(all_hyps)
        #"""

    def combine_parses(self, nbest_parses):
        """TODO - should return a list of tuples (semantic act, prob) - in order
        """
        #TODO  JUST A HACK FOR NOW - needs to combine probs and order to get single most likely semantic hypothesis
        # Should probably also be ammending self.clean() or doing what it does here or ...
        # will work for now on assumption that there was only 1 sentence (not an nbest list) to parse anyway
        return nbest_parses 

    def decode_single_hypothesis(self,obs):
        """
        :param: (str) obs - sentence (an ASR hypothesis)
        """ 
        self.semanticActs = []
        # run the obs thru all possible semantic acts:
        self._decode_request(obs)
        self._decode_ack(obs)
        self._decode_inform(obs)
        self._decode_confirm(obs)
        self._decode_hello(obs)
        self._decode_negate(obs)
        self._decode_repeat(obs)
        self._decode_reqalts(obs)
        self._decode_bye(obs)
        self._decode_type(obs)
        # probably need to then do some cleaning on acts in semanticActs
        self.clean()
        return self.semanticActs

    def init_regular_expressions(self):
        """
        """
        self.rHELLO = "(\b|^|\ )(hi|hello)\s"
        self.rNEG = "(\b|^|\ )(no|wrong|incorrect|error)|not\ (true|correct|right)\s" 
        self.rACK = "(yes|ok|okay|sure)" 
        self.rBYE = "(\b|^|\ )(bye|goodbye|that'*s*\ (is\ )*all)(\s|$|\ )" 
        self.rREQALTS = "(\b|^|\ )((something|anything)\ else)|(different(\ one)*)|(another\ one)|(alternatives*)|"
        self.rREQALTS += "(other options*)|((don\'*t|do not) (want|like)\ (that|this)(\ one)*)" 
        self.rREPEAT = "(\b|^|\ )(repeat\ that)|(say\ that\ again)" 
        # The remaining regex are for the slot,value dependent acts - and so here in the base class are \
        # just aiming to catch intent.
        # REQUESTS:
        self.WHAT = "(what\'*s*|which|does|where)(\ its)*"
        self.IT = "(it\'*s*|it\ have|is\ it\'*s*|is\ the)(\ for)*"
        self.CYTM = "(can\ you\ tell\ me\ (the|it\'*s))"
        self.NEGATE ="((i\ )*(don\'*t|do\ not|does\ not|does\'*nt)\ (care|mind|matter)(\ (about|what))*(\ (the|it\'*s*))*)"
        self.DONTCARE = "(i\ dont\ care\ )" #Cant create variable lengths with negative lookback... else merge following:
        self.DONTCAREWHAT = "(i\ dont\ care\ what\ )"
        self.DONTCAREABOUT = "(i\ dont\ care\ about\ )"  
        self.rREQUEST = "(\b|^|\ )(?<!"+self.DONTCARE+")("+self.WHAT+"\ "+self.IT+"|"+self.CYTM+")"
        # INFORMS:
        self.WANT = "(want|have|need|looking\ for|used\ for)(\ a)*"
        self.WBG = "(\ would\ be\ (good|nice))"
        self.rINFORM = "(\b|^|\ )"+self.WANT
        self.rINFORM_DONTCARE = self.DONTCARE+r"((what|which|about)(\ (it\'*s*|the))*)+" 
        self.rINFORM_DONTWANT = r"(((i\ )*(don\'*t\ want))|it\ (shouldn\'*t|should\ not)\ (have|be))+" 


    def _decode_request(self,obs):
        """TO BE DEFINED IN DOMAIN SPECIFIC WAY IN DERIVED CLASS"""
        pass

    def _decode_inform(self,obs):
        """TO BE DEFINED IN DOMAIN SPECIFIC WAY IN DERIVED CLASS"""
        pass

    def _decode_confirm(self, obs):
        """TO BE DEFINED IN DOMAIN SPECIFIC WAY IN DERIVED CLASS"""
        pass

    def _decode_type(self,obs):
        """TO BE DEFINED IN DOMAIN SPECIFIC WAY IN DERIVED CLASS"""
        pass

    def _decode_hello(self,obs):
        """
        """  
        if self._check(re.search(self.rHELLO,obs, re.I)): #DEL is not None:
            self.semanticActs.append('hello()')

    def _decode_negate(self, obs):
        """
        """
        if self._check(re.search(self.rNEG,obs, re.I)): #DEL  is not None:
            self.semanticActs.append('negate()')  #TODO - is this a used act? syntax: neg()?

    def _decode_ack(self,obs):
        """
        """ 
        if self._check(re.search(self.rACK,obs, re.I)): #DEL is not None:
            self.semanticActs.append('ack()')

    def _decode_bye(self, obs):
        """
        """
        if self._check(re.search(self.rBYE,obs, re.I)): #DEL is not None:
            self.semanticActs.append('bye()')

    def _decode_reqalts(self,obs):
        """
        """
        if self._check(re.search(self.rREQALTS,obs, re.I)): #DEL is not None:
            self.semanticActs.append('reqalts()')

    def _decode_repeat(self, obs):
        """
        """
        if self._check(re.search(self.rREPEAT,obs, re.I)): #DEL is not None:
            self.semanticActs.append('repeat()')

    def clean(self):
        """
        """
        #TODO - deal with duplicates, probabilities, others?
        self.semanticActs =  "|".join(self.semanticActs)

    def _contextual_inform(self,obs):
        """
        """
        # Statements that are contextual/implicit (ie dont mention slot or value explicitly):
        rCONTEXTUAL_DONTCARE = r"(anything|any|(i\ )*dont\ care)$" 
        if self._check(re.search(rCONTEXTUAL_DONTCARE, obs, re.I)): #DEL is not None: 
            self.semanticActs.append('inform(=dontcare)')

    def _domain_independent_requests(self,obs):
        """  
        """
        rDOM_IN_REQ_NAME = r"((what(s*)|what\ is)\ it called)"
        if self._check(re.search(rDOM_IN_REQ_NAME, obs, re.I)): #DEL is not None: 
            self.semanticActs.append('request(name)')

    def _check(self,re_object):
        """
        """
        if re_object is None:
            return False
        for o in re_object.groups():
            if o is not None:
                return True
        return False


class FileParser():
    """
    """
    def __init__(self,filename, domainTag="TT", repoRoot=None):
        self.domain_tag = domainTag
        self.filename=filename
        self.JOINER = " <=> "
        # TODO - note that can import parser into Hubs via below 2 lines:
        parser_module = __import__("RegexSemI_"+self.domain_tag, fromlist=["RegexSemI_"+self.domain_tag]) 
        self.parser = getattr(parser_module, "RegexSemI_"+self.domain_tag)(repoIn=repoRoot)

    def decode_file(self, DOPRINT=True):
        """
        """
        self.inputs = []
        self.results = []
        with open(self.filename,"r") as f:
            for line in f:
                parse = (line.strip('\n'), self.parser.decode(line)[0][0])
                self.results.append(parse[1]) #list order is persistent, as required here
                self.inputs.append(parse[0])
                if DOPRINT:
                    print parse[0] + self.JOINER + parse[1]

    def test_file(self, referenceFile=None):
        """Note this just has some **very basic checking** that the ref and parsed file match up appropriately. 
                ------------------------------------------------------------ 
        A guide to using this function for developing Regex SemI parsers:
        0. create a list of example sentences for parsing
        1. get a parser working a little
        2. Dump the output of parsing the example sentences file 
        >> python RegexSemI.py _resources/EXAMPLE_INPUT_SENTENCES_FOR_DOMAIN DOMAINTAG PATH_TO_REPO_ROOT > OUTfile
        3. Fix the semantic parsers in the OUTfile so that it can be used as a reference 
        4. Improve the parser
        5. Check the improvements against the reference OUTfile
        >> python RegexSemI.py _resources/EXAMPLE_INPUT_SENTENCES_FOR_DOMAIN DOMAINTAG PATH_TO_REPO_ROOT OUTfile
        6. go back to 4, add more sentences to examples file etc etc
        """
        if referenceFile is None:
            return
        lineNum = -1
        with open(referenceFile,"r") as f:
            for line in f:
                lineNum += 1
                line = line.strip('\n')
                bits = line.split(self.JOINER)
                assert(len(bits)==2)
                userinput,reference = bits[0],bits[1]
                if userinput != self.inputs[lineNum]:
                    print "MISMATCH ERROR: " + userinput + " != "  + self.inputs[lineNum]
                elif self.results[lineNum] != reference:
                    print "INCORRECT PARSE: " + self.results[lineNum] + " != "  + reference
                else:
                    pass
                    #print "CORRECT: " + self.results[lineNum] + self.JOINER + reference
                


#-------------------------------------------------------------------------------------------
#  Main
#-------------------------------------------------------------------------------------------
if __name__=="__main__":
    import sys
    if len(sys.argv) < 4:
        exit("Usage: python RegexSemi.py EXAMPLE_SENTENCES_FILEPATH DOMAIN_TAG REPOSITORY_ROOT [optional: REFERENCE_FILE]")
    if len(sys.argv) == 5:
        refFileIn = sys.argv[4]
    else:
        refFileIn = None
    fp = FileParser(filename=sys.argv[1], domainTag=sys.argv[2], repoRoot=sys.argv[3])
    fp.decode_file(DOPRINT=refFileIn is None)
    fp.test_file(referenceFile=refFileIn)


#END OF FILE
