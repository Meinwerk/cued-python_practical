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
SemO.py - Semantic Output
============================

Authors: Dongho Kim, David Vandyke  (Copyright CUED Dialogue Systems Group 2015)

**Basic Usage**: 
    >>> import SemO
    >>> semo = SemO.PassthroughSemO()

.. seealso:: CUED Imports/Dependencies: 

    import :class:`Settings` |.|
    import :class:`DiaAct` |.|
    import :class:`Scanner` |.|
    import :class:`ContextLogger`

************************

'''
__author__ = "donghokim, davidvandyke"

import tokenize
from collections import defaultdict
import re
import copy

import Settings
import DiaAct
import ContextLogger
logger = ContextLogger.getLogger(__name__)


class PassthroughSemO():
    def __init__(self):
        pass

    def generate(self, act):
        return act


def parse_output(input_string):
    '''Utility function used within this file's classes. 

    :param input_string: (str) 
    '''
    import Scanner
    output_scanner = Scanner.Scanner(input_string)
    output_scanner.next()
    words = []
    while output_scanner.cur[0] != tokenize.ENDMARKER:
        if output_scanner.cur[0] == tokenize.NAME:
            words.append(output_scanner.cur[1])
            output_scanner.next()
        elif output_scanner.cur[1] == '$':
            variable = '$'
            output_scanner.next()
            variable += output_scanner.cur[1]
            words.append(variable)
            output_scanner.next()
        elif output_scanner.cur[1] == '%':
            function = '%'
            output_scanner.next()
            while output_scanner.cur[1] != ')':
                function += output_scanner.cur[1]
                output_scanner.next()
            function += output_scanner.cur[1]
            words.append(function)
            output_scanner.next()
        else:
            words[-1] += output_scanner.cur[1]
            output_scanner.next()
    return words


class BasicTemplateRule():
    '''
    The template rule corresponds to a single line in a template rules file.
    This consists of an act (including non-terminals) that the rule applies to with an output string to generate
    (again including non-terminals).
    Example::
    
        select(food=$X, food=dontcare) : "Sorry would you like $X food or you dont care";
         self.rue_items = {food: [$X, dontcare]}
    '''
    def __init__(self, scanner):
        '''
        Reads a template rule from the scanner. This should have the form 'act: string' with optional comments.
        '''
        import Scanner

        self.rule_act = self.read_from_stream(scanner)
        rule_act_str = str(self.rule_act)

        if '))' in rule_act_str:
            logger.warning('Two )): ' + rule_act_str)
        if self.rule_act.act == 'badact':
            logger.error('Generated bac act rule: ' + rule_act_str)

        scanner.check_token(':', 'Expected \':\' after ' + rule_act_str)
        scanner.next()
        if scanner.cur[0] not in [tokenize.NAME, tokenize.STRING]:
            raise SyntaxError('Expected string after colon')

        # Parse output string.
        self.output = scanner.cur[1].strip('"\'').strip()
        self.output_list = parse_output(self.output)

        scanner.next()
        scanner.check_token(';', 'Expected \';\' at the end of string')
        scanner.next()

        # rule_items = {slot: [val1, val2, ...], ...}
        self.rule_items = defaultdict(list)
        for item in self.rule_act.items:
            self.rule_items[item.slot].append(item.val)

    def __str__(self):
        s = str(self.rule_act)
        s += ' : '
        s += self.output + ';'
        return s

    def read_from_stream(self, scanner):
        sin = ''
        while scanner.cur[1] != ';' and scanner.cur[0] != tokenize.ENDMARKER and scanner.cur[1] != ':':
            sin += scanner.cur[1]
            scanner.next()
        return DiaAct.DiaAct(sin)

    def generate(self, input_act):
        '''
        Generates a text from using this rule on the given input act.
        Also edits the passed variables to store the number of matched items,
        number of missing items and number of matched utterance types.
        Note that the order of the act and rule acts must be exactly the same.

        :returns: output, match_count, missing_count, type_match_count
        '''
        type_match_count = 0
        match_count = 0
        missing_count = 0
        non_term_map = {}
        if self.rule_act.act == input_act.act:
            type_match_count += 1
            match_count, missing_count, non_term_map = self.match_act(input_act)

        return self.generate_from_map(non_term_map), match_count, missing_count, type_match_count, non_term_map

    def generate_from_map(self, non_term_map):
        '''
        Does the generation by substituting values in non_term_map.

        :param non_term_map: {$X: food, ...}
        :return: list of generated words
        '''
        num_missing = 0
        word_list = copy.deepcopy(self.output_list)

        for i, word in enumerate(word_list):
            if word[0] == '$': # Variable $X
                if word not in non_term_map:
                    # logger.debug('%s not found in non_term_map %s.' % (word, str(non_term_map)))
                    num_missing += 1
                else:
                    word_list[i] = non_term_map[word]
            # %$ function in output will be transformed later.

        return word_list

    def match_act(self, act):
        '''
        This function matches the given act against the slots in rule_map
        any slot-value pairs that are matched will be placed in the non-terminal map.

        :param act: The act to match against (i.e. the act that is being transformed, with no non-terminals)
        :returns (found_count, num_missing): found_count = # of items matched, num_missing = # of missing values.
        '''
        non_term_map = {} # Any mathced non-terminals are placed here.
        rules = {}
        dollar_rules = {}
        for slot in self.rule_items:
            if slot[0] == '$':
                # Copy over rules that have an unspecified slot.
                value_list = copy.deepcopy(self.rule_items[slot])
                if len(value_list) > 1:
                    logger.error('Non-terminal %s is mapped to multiple values %s' % (slot, str(value_list)))
                dollar_rules[slot] = value_list[0]
            else:
                # Copy over rules that have a specified slot.
                rules[slot] = copy.deepcopy(self.rule_items[slot])

        logger.debug(' rules: ' + str(rules))
        logger.debug('$rules: ' + str(dollar_rules))

        found_count = 0
        # For each item in the given system action.
        for item in act.items:
            found = False
            if item.slot in rules:
                if item.val in rules[item.slot]:
                    # Found this exact terminal in the rules. (e.g. food=none)
                    found = True
                    found_count += 1
                    rules[item.slot].remove(item.val)
                else:
                    # Found the rule containing the same slot but no terminal.
                    # Use the first rule which has a non-terminal.
                    val = None
                    for value in rules[item.slot]:
                        if value[0] == '$':
                            # Check if we've already assigned this non-terminal.
                            if value not in non_term_map:
                                found = True
                                val = value
                                break
                            elif non_term_map[value] == item.val:
                                # This is a non-terminal so we can re-write it if we've already got it.
                                # Then this value is the same so that also counts as found.
                                found = True
                                val = value
                                break

                    if found:
                        non_term_map[val] = item.val
                        rules[item.slot].remove(val)
                        found_count += 1

            if not found and len(dollar_rules) > 0:
                # The slot doesn't match. Just use the first dollar rule.
                for slot in dollar_rules:
                    if item.val == dollar_rules[slot]: # $X=dontcare
                        found = True
                        non_term_map[slot] = item.slot
                        del dollar_rules[slot]
                        found_count += 1
                        break

                if not found:
                    for slot in dollar_rules:
                        if dollar_rules[slot] is not None and dollar_rules[slot][0] == '$': # $X=$Y
                            found = True
                            non_term_map[slot] = item.slot
                            non_term_map[dollar_rules[slot]] = item.val
                            del dollar_rules[slot]
                            found_count += 1
                            break

        num_missing = len([val for sublist in rules.values() for val in sublist])
        return found_count, num_missing, non_term_map


class BasicTemplateFunction():
    '''
    A function in the generation rules that converts a group of inputs into an output string.
    The use of template functions allows for simplification of the generation file as the way
    a given group of variables is generated can be extended over multiple rules.
        
    The format of the function is::

        %functionName($param1, $param2, ...) {
            p1, p2, ... : "Generation output";}

    :param scanner: (instance) of :class:`Scanner`
    '''
    def __init__(self, scanner):
        scanner.check_token('%', 'Expected map variable name (with %)')
        scanner.next()
        self.function_name = '%'+scanner.cur[1]
        scanner.next()
        scanner.check_token('(', 'Expected open bracket ( after declaration of function')

        self.parameter_names = []
        while True:
            scanner.next()
            # print scanner.cur
            if scanner.cur[1] == '$':
                scanner.next()
                self.parameter_names.append(scanner.cur[1])
            elif scanner.cur[1] == ')':
                break
            elif scanner.cur[1] != ',':
                raise SyntaxError('Expected variable, comma, close bracket ) in input definition of tempate function rule')

        if len(self.parameter_names) == 0:
            raise SyntaxError('Must have some inputs in function definition: ' + self.function_name)

        scanner.next()
        scanner.check_token('{', 'Expected open brace after declaration of function ' + self.function_name)
        scanner.next()

        self.rules = []
        while scanner.cur[1] != '}':
            new_rule = BasicTemplateFunctionRule(scanner)
            if len(new_rule.inputs) != len(self.parameter_names):
                raise SyntaxError('Different numbers of parameters (%d) in rules and definition (%d) for function: %s' %
                                  (len(new_rule.inputs), len(self.parameter_names), self.function_name))
            self.rules.append(new_rule)
        scanner.next()

    def transform(self, inputs):
        '''
        :param inputs: Array of function arguments.
        :returns: None
        '''
        for rule in self.rules:
            if rule.is_applicable(inputs):
                return rule.transform(inputs)

        logger.error('In function %s: No rule to transform inputs %s' % (self.function_name, str(inputs)))


class BasicTemplateFunctionRule():
    '''
    A single line of a basic template function. This does a conversion of a group of values into a string.
    e.g. p1, p2, ... : "Generation output"

    :param scanner: (instance) of :class:`Scanner`
    '''
    def __init__(self, scanner):
        '''
        Loads a template function rule from the stream. The rule should have the format:
            input1, input2 : "output string";
        '''
        self.inputs = []
        self.input_map = {}
        while True:
            # print scanner.cur
            if scanner.cur[1] == '$' or scanner.cur[0] in [tokenize.NUMBER, tokenize.STRING, tokenize.NAME]:
                input = scanner.cur[1]
                if scanner.cur[1] == '$':
                    scanner.next()
                    input += scanner.cur[1]
                # Add to lookup table.
                self.input_map[input] = len(self.inputs)
                self.inputs.append(input.strip('"\''))
                scanner.next()
            elif scanner.cur[1] == ':':
                scanner.next()
                break
            elif scanner.cur[1] == ',':
                scanner.next()
            else:
                raise SyntaxError('Expected string, comma, or colon in input definition of template function rule.')

        if len(self.inputs) == 0:
            raise SyntaxError('No inputs specified for template function rule.')

        # Parse output string.
        scanner.check_token(tokenize.STRING, 'Expected string output for template function rule.')
        self.output = scanner.cur[1].strip('\"').strip()
        self.output = parse_output(self.output)

        scanner.next()
        scanner.check_token(';', 'Expected semicolon to end template function rule.')
        scanner.next()

    def __str__(self):
        return str(self.inputs) + ' : ' + str(self.output)

    def is_applicable(self, inputs):
        '''
        Checks if this function rule is applicable for the given inputs.

        :param inputs: array of words
        :returns: (bool) 
        '''
        if len(inputs) != len(self.inputs):
            return False

        for i, word in enumerate(self.inputs):
            if word[0] != '$' and inputs[i] != word:
                return False

        return True

    def transform(self, inputs):
        '''
        Transforms the given inputs into the output. All variables in the output list are looked up in the map
        and the relevant value from the inputs is chosen.

        :param inputs: array of words.
        :returns: Transformed string.
        '''
        result = []
        for output_word in self.output:
            if output_word[0] == '$':
                if output_word not in self.input_map:
                    logger.error('Could not find variable %s' % output_word)
                result.append(inputs[self.input_map[output_word]])
            else:
                result.append(output_word)
        return ' '.join(result)


class BasicTemplateGenerator():
    '''
    The basic template generator loads a list of template-based rules from a string.
    These are then applied on any input dialogue act and used to generate an output string.

    :param filename: (str) the template rules file
    '''
    def __init__(self, filename):
        import Scanner
        f = open(filename)
        string = f.read()
        string.replace('\t', ' ')
        file_without_comment = Scanner.remove_comments(string)
        scanner = Scanner.Scanner(file_without_comment)
        scanner.next()
        self.rules = []
        self.functions = []
        self.function_map = {}
        self.parse_rules(scanner)
        f.close()

    def parse_rules(self, scanner):
        '''Check the given rules

        :param scanner: (instance) of :class:`Scanner`
        '''
        try:
            while scanner.cur[0] not in [tokenize.ENDMARKER]:
                if scanner.cur[0] == tokenize.NAME:
                    self.rules.append(BasicTemplateRule(scanner))
                elif scanner.cur[1] == '%':
                    ftn = BasicTemplateFunction(scanner)
                    self.functions.append(ftn)
                    self.function_map[ftn.function_name] = ftn
                else:
                    raise SyntaxError('Expected a string or function map but got ' +
                                      scanner.cur[1] + ' at this position while parsing generation rules.')

        except SyntaxError as inst:
            print inst

    def transform(self, input):
        '''
        Transforms the input from a semantic utterance form to a text form using the rules in the generator.
        This function will run the input through all variable rules and will choose the best one according to the
        number of matched act types, matched items and missing items.

        :param input: (str) input system action (semantic form).
        :returns: (str) natural language 
        '''
        input_utt = DiaAct.DiaAct(input)

        # Iterate over BasicTemplateRule rules.
        best_rule = None
        best = None
        best_matches = 0
        best_type_match = 0
        best_missing = 1000
        best_non_term_map = None
        for rule in self.rules:
            logger.debug('Checking Rule %s' % str(rule))
            out, matches, missing, type_match, non_term_map = rule.generate(input_utt)
            if type_match > 0:
                logger.debug('Checking Rule %s: type_match=%d, missing=%d, matches=%d, output=%s' %
                             (str(rule), type_match, missing, matches, ' '.join(out)))

            # Pick up the best rule.
            choose_this = False
            if type_match > 0:
                if missing < best_missing:
                    choose_this = True
                elif missing == best_missing:
                    if type_match > best_type_match:
                        choose_this = True
                    elif type_match == best_type_match and matches > best_matches:
                        choose_this = True

            if choose_this:
                best_rule = rule
                best = out
                best_missing = missing
                best_type_match = type_match
                best_matches = matches
                best_non_term_map = non_term_map

                if best_type_match == 1 and best_missing == 0 and best_matches == len(input_utt.items):
                    break

        if best_rule is not None:
            if best_missing > 0:
                logger.warning('While transforming %s, there were missing items.' % input)
        else:
            logger.debug('No rule used.')

        best = self.compute_ftn(best, best_non_term_map)
        return ' '.join(best)

    def compute_ftn(self, input_words, non_term_map):
        '''
        Applies this function to convert a function into a string.

        :param input_words: (list) of generated words. Some words might contain function. `(e.g. %count_rest($X) or %$Y_str($P) ...)`
        :param non_term_map:  
        :returns: (list) modified input_words
        '''
        for i, word in enumerate(input_words):
            if '%' not in word:
                continue
            logger.debug('Processing %s in %s...' % (word, str(input_words)))
            m = re.search('^([^\(\)]*)\((.*)\)(.*)$', word.strip())
            if m is None:
                logger.error('Parsing failed in %s' % word.strip())
            ftn_name = m.group(1)
            ftn_args = [x.strip() for x in m.group(2).split(',')]
            remaining = ''
            if len(m.groups()) > 2:
                remaining = m.group(3)

            # Processing function name.
            if '$' in ftn_name:
                tokens = ftn_name.split('_')
                if len(tokens) > 2:
                    logger.error('More than one underbar _ found in function name %s' % ftn_name)
                var = tokens[0][1:]
                if var not in non_term_map:
                    logger.error('Unable to find nonterminal %s in non terminal map.' % var)
                ftn_name = ftn_name.replace(var, non_term_map[var])

            # Processing function args.
            for j, arg in enumerate(ftn_args):
                if arg[0] == '%':
                    logger.error('% in function argument %s' % str(word))
                elif arg[0] == '$':
                    ftn_args[j] = non_term_map[arg]

            if ftn_name not in self.function_map:
                logger.error('Function name %s is not found.' % ftn_name)
            else:
                input_words[i] = self.function_map[ftn_name].transform(ftn_args) + remaining

        return input_words


class BasicSemO():
    '''
    Template-based output generator.

    :parameter [basicsemo] templatefile: The template file to use for generation.
    :parameter [basicsemo] emphasis: Generate emphasis tags.
    :parameter [basicsemo] emphasisopen: Emphasis open tag (default: &ltEMPH&lt).
    :parameter [basicsemo] emphasisclose: Emphasis close tag (default: &lt/EMPH&lt).
    '''
    def __init__(self):
        configs = []
        template_filename = None
        if Settings.config.has_option('basicsemo', 'templatefile'):
            configs.append('templatefile')
            template_filename = str(Settings.config.get('basicsemo', 'templatefile'))
        self.emphasis = False
        if Settings.config.has_option('basicsemo', 'emphasis'):
            configs.append('emphasis')
            self.emphasis = Settings.config.getboolean('basicsemo', 'emphasis')
        self.emphasis_open = '<EMPH>'
        if Settings.config.has_option('basicsemo', 'emphasisopen'):
            configs.append('emphasisopen')
            self.emphasis = Settings.config.get('basicsemo', 'emphasisopen')
        self.emphasis_close = '</EMPH>'
        if Settings.config.has_option('basicsemo', 'emphasisclose'):
            configs.append('emphasisclose')
            self.emphasis = Settings.config.get('basicsemo', 'emphasisclose')

        if Settings.config.has_section('basicsemo'):
            for opt in Settings.config.options('basicsemo'):
                if opt not in configs and opt not in Settings.config.defaults():
                    logger.error('Invalid config: '+opt)

        self.generator = BasicTemplateGenerator(template_filename)

    def generate(self, act):
        if self.emphasis:
            logger.warning('Emphasis is not implemented.')

        return self.generator.transform(act)


class SemOManager():
    #TODO
    """
    """
    def _init_(self):
        pass


if __name__ == '__main__':
    BasicTemplateGenerator('config/TopTableMessages.txt')


#END OF FILE
