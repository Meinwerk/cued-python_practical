'''
Rules.py - read text based rules file 
====================================================

Author: Dongho Kim  (Copyright CUED Dialogue Systems Group 2015)

.. warning::
    Not currently imported by any file. Ontology is now represented as a json object, e.g. config/toptable.json and read by :class:`Settings` into the global 'ontology'.

.. seealso:: CUED Imports/Dependencies: 

    import :class:`Scanner`

************************

'''

import tokenize
import Scanner
import pprint


class ClassInst():
    '''Utility Class: instances
    '''
    def __init__(self,scanner):
        scanner.check_token(tokenize.NAME, 'Class ist name expected')
        self.path = scanner.cur[1]
        scanner.next()

    def __str__(self):
        return 'class(%s)' % self.path


class ClassDef():
    '''Utility Class: definitions
    '''
    def __init__(self, scanner, class_inst):
        # Parse subclass if any.
        self.subclass = None
        if scanner.cur[0] == tokenize.NAME:
            self.subkey_type = 'generalKey'
            self.subclass = scanner.cur[1]
            scanner.next()

        elif scanner.cur[1] == '+':
            self.subkey_type = 'selectKey'
            scanner.next()
            self.subclass = scanner.cur[1]
            scanner.next()

        # Parse class body if any.
        self.args = []
        if scanner.cur[1] == '(':
            scanner.next()
            if scanner.cur[1] != ')':
                self.args.append(ClassArg(scanner))
                while scanner.cur[1] == ',':
                    scanner.next()
                    self.args.append(ClassArg(scanner))
            scanner.check_token(')', ') expected in class body')
            scanner.next()

        # Check that at least a subclass or a body was given.
        if self.subclass is None and len(self.args) == 0:
            raise SyntaxError('Class def has no subclass and no body.')

        # Parse condition if any.
        self.cond = None
        if scanner.cur[1] == '[':
            self.cond = Condition(scanner)

        # Parse probability if any.
        self.prob = -1.0
        if scanner.cur[1] == '{':
            scanner.next()
            scanner.check_token(tokenize.NUMBER, 'Probability expected')
            self.prob = scanner.cur[1]
            scanner.next()
            scanner.check_token('}', '} expected')
            scanner.next()

    def __repr__(self):
        return str(self)

    def __str__(self):
        s = 'ClassDef(%s, %s)' % (self.subclass, self.subkey_type)
        s += '('
        str_list = []
        for arg in self.args:
            str_list.append(str(arg))
        s += ', '.join(str_list)
        s += ')'
        return s


class ClassArg():
    '''Utility Class: arguments
    '''
    def __init__(self, scanner):
        # scanner.check_token(['-', '+', tokenize.NAME, '*', '~'], 'Class arg expected')
        self.keytype = 'generalKey'
        if scanner.cur[1] == '*':
            self.keytype = 'interKey'
            scanner.next()
        elif scanner.cur[1] == '-':
            self.keytype = 'infoKey'
            scanner.next()
        elif scanner.cur[1] == '+':
            self.keytype = 'selectKey'
            scanner.next()
        elif scanner.cur[1] == '~':
            self.keytype = 'structKey'
            scanner.next()

        # Parse term.
        self.term = TermDef(scanner)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return str(self.term) + '_' + str(self.keytype)


class TermDef():
    '''Utility Class: term definitions
    '''
    def __init__(self, scanner):
        scanner.check_token(tokenize.NAME, 'Term functor expected')
        self.name = scanner.cur[1]
        scanner.next()

    def __str__(self):
        return self.name


class LexDef():
    '''Utility Class: lexical definitions
    '''
    def __init__(self, scanner):
        self.atoms = []

        scanner.check_token('=', '= expected in scanner def')
        scanner.next()

        # Parse atom list.
        scanner.check_token('(', '( expected')
        scanner.next()

        # Special number of descriptive lex type.
        if scanner.cur[0] == tokenize.NUMBER:
            self.lextype = 'numericLex'
            scanner.next()
        elif scanner.cur[1] == ')':
            self.lextype = 'descriptiveLex'

        else:
            # Regular atomic lex type.
            self.lextype = 'atomicLex'
            self.atoms.append(AtomDef(scanner))
            while scanner.cur[1] == '|':
                scanner.next()
                self.atoms.append(AtomDef(scanner))

        scanner.check_token(')', '| or ) expected')
        scanner.next()

        # Add dontcare atom.
        if self.lextype == 'atomicLex':
            self.atoms.append(AtomDef('dontcare'))

        # Normalise probability - deprecated.


class AtomDef():
    '''Utility Class: atom definitions
    '''
    def __init__(self, scanner):
        if type(scanner) in [str, unicode]:
            self.name = scanner
        else:
            self.name = scanner.cur[1]
            scanner.next()

            # Parse probability if any.
            if scanner.cur[1] == '{':
                scanner.next()
                scanner.check_token(tokenize.NUMBER, 'Probability expected')
                self.prior = scanner.cur[1]
                scanner.next()
                scanner.check_token('}', '} expected')
                scanner.next()

        if type(self.name) in [str, unicode]:
            self.name = self.name.lower()


def parse_rules(scanner):
    '''Parse rules file

    :param scanner: (:class:`Scanner`)
    :returns: (list) classes, (list) lexes 
    '''
    classes = []
    lexes = []
    try:
        while scanner.cur[0] not in [tokenize.ENDMARKER, tokenize.PLUS]:
            # Parse a single rule.
            # First, get class inst.
            # print scanner.cur
            p = ClassInst(scanner)
            # Check if it is a class or lex then parse rhs of rule.
            if scanner.cur[1] == '-':
                scanner.next()
                scanner.check_token('>', '> expected')
                scanner.next()

                # Parse class definition
                classes.append(ClassDef(scanner, p))

            else:
                # Parse scanner definition
                lexes.append(LexDef(scanner))

            scanner.check_token(';', '; expected')
            scanner.next()
        
        # djv27 checking ... Rules.py seemingly not used. grep -r "import rules" * gives nothing 
        print classes
        raw_input('classes')
        print lexes
        raw_input('lexes')
        return classes, lexes
    except SyntaxError as inst:
        print inst
        # if token[0] is tokenize.STRING:
        #     return 'string'
        # elif token[0] is tokenize.NUMBER:
#     return 'number'


def load_rules(rule_file):
    '''Directly calls :class:`parse_rules` whose scanner acts on rule_file read as a string. 

    :param rule_file: (str) path to rules file
    :returns: (list) classes, (list) lexes
    '''
    f = open(rule_file)
    string = f.read()
    string.replace('\t', ' ')
    file_without_comment = Scanner.remove_comments(string)
    scanner = Scanner.Scanner(file_without_comment)
    scanner.next()
    classes, lexes = parse_rules(scanner)
    f.close()
    return classes, lexes
    # pprint.pprint(str(classes))
    # pprint.pprint(str(lexes))

if __name__ == '__main__':
    load_rules('config/TTrules.txt')
