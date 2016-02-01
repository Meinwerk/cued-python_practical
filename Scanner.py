'''
Scanner.py - string scanning utility 
====================================================

Author: Dongho Kim  (Copyright CUED Dialogue Systems Group 2015)

************************

'''

import cStringIO
import tokenize


def remove_comments(src):
    """
    This reads tokens using tokenize.generate_tokens and recombines them
    using tokenize.untokenize, and skipping comment/docstring tokens in between
    """
    f = cStringIO.StringIO(src)
    class SkipException(Exception): pass
    processed_tokens = []
    last_token = None
    # go thru all the tokens and try to skip comments and docstrings
    for tok in tokenize.generate_tokens(f.readline):
        t_type, t_string, t_srow_scol, t_erow_ecol, t_line = tok

        try:
            if t_type == tokenize.COMMENT:
                raise SkipException()

            elif t_type == tokenize.STRING:

                if last_token is None or last_token[0] in [tokenize.INDENT]:
                    # FIXEME: this may remove valid strings too?
                    #raise SkipException()
                    pass

        except SkipException:
            pass
        else:
            processed_tokens.append(tok)

        last_token = tok

    return tokenize.untokenize(processed_tokens)


class Scanner():
    def __init__(self, string):
        src = cStringIO.StringIO(string).readline
        self.tokens = tokenize.generate_tokens(src)
        self.cur = None

    def next(self):
        while True:
            self.cur = self.tokens.next()
            if self.cur[0] not in [54, tokenize.NEWLINE] and self.cur[1] != ' ':
                break
        return self.cur

    def check_token(self, token, message):
        if type(token) == int:
            if self.cur[0] != token:
                raise SyntaxError(message + '; token: %s' % str(self.cur))
        else:
            if self.cur[1] != token:
                raise SyntaxError(message + '; token: %s' % str(self.cur))
