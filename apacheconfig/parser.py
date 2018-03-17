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
        p[0] = ('comment', p[1])

    def p_statement(self, p):
        """statement : STRING '=' STRING
                     | STRING STRING
        """
        if len(p) == 4:
            p[0] = ('option', p[1], p[3])
        else:
            p[0] = ('option', p[1],  p[2])

    def p_statements(self, p):
        """statements : statements statement
                      | statements comment
                      | statement
                      | comment
        """
        n = len(p)
        if n == 3:
            p[0] = p[1] + [p[2]]
        elif n == 2:
            p[0] = [p[1]]

    def p_block(self, p):
        """block : OPEN_TAG statements CLOSE_TAG
                 | OPEN_TAG CLOSE_TAG
        """
        if len(p) == 4:
            p[0] = ('block', p[1], p[2], p[3])
        else:
            p[0] = ('block', p[1],  (), p[2])

    def p_config(self, p):
        """config : config statements
                  | config comment
                  | config block
                  | statements
                  | comment
                  | block
        """
        n = len(p)
        if n == 3:
            p[0] = p[1] + [p[2]]
        elif n == 2:
            p[0] = [p[1]]

    def p_error(self, p):
        raise ApacheConfigError("Parser error at '%s'" % p.value)
