#
# This file is part of apacheconfig software.
#
# Copyright (c) 2018, Ilya Etingof <etingof@gmail.com>
# License: https://github.com/etingof/apacheconfig/LICENSE.rst
#
import logging
import ply.yacc as yacc

from apacheconfig.error import ApacheConfigError

log = logging.getLogger(__name__)


class ApacheConfigParser(object):

    def __init__(self, lexer, start='config', tempdir=None, debug=False):
        self._lexer = lexer
        self.tokens = lexer.tokens  # parser needs this implicitly
        self._tempdir = tempdir
        self._debug = debug
        self._start = start
        self.engine = None
        self.reset()

    def reset(self):
        self.engine = yacc.yacc(
            module=self,
            start=self._start,
            outputdir=self._tempdir,
            write_tables=bool(self._tempdir),
            debug=False,
            debuglog=log if self._debug else None,
            errorlog=log if self._debug else None
        )

    def parse(self, text):
        self.reset()
        return self.engine.parse(text)

    # Parsing rules

    def p_comment(self, p):
        """comment : COMMENT
        """
        p[0] = ['comment', p[1]]

    def p_statement(self, p):
        """statement : STRING '=' STRING
                     | STRING STRING
        """
        if len(p) == 4:
            p[0] = ['statement', p[1], p[3]]
        else:
            p[0] = ['statement', p[1], p[2]]

    def p_statements(self, p):
        """statements : statements statement
                      | statement
        """
        n = len(p)
        if n == 3:
            p[0] = p[1] + [p[2]]
        elif n == 2:
            p[0] = ['statements', p[1]]

    def p_contents(self, p):
        """contents : contents statements
                    | contents comment
                    | contents block
                    | statements
                    | comment
                    | block
        """
        n = len(p)
        if n == 3:
            p[0] = p[1] + [p[2]]
        else:
            p[0] = ['contents', p[1]]

    def p_block(self, p):
        """block : OPEN_TAG contents CLOSE_TAG
                 | OPEN_TAG CLOSE_TAG
                 | OPEN_CLOSE_TAG
        """
        n = len(p)
        if n == 4:
            p[0] = ['block', p[1], p[2], p[3]]
        elif n == 3:
            p[0] = ['block', p[1],  [], p[2]]
        else:
            p[0] = ['block', p[1], [], p[1]]

    def p_config(self, p):
        """config : config contents
                  | contents
        """
        n = len(p)
        if n == 3:
            p[0] = p[1] + [p[2]]
        elif n == 2:
            p[0] = ['config', p[1]]

    def p_error(self, p):
        raise ApacheConfigError("Parser error at '%s'" % p.value if p else '?')
