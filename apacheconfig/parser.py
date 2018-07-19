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


class HashCommentsParser(object):
    def p_hashcomment(self, p):
        """comment : HASHCOMMENT
        """
        p[0] = ['comment', p[1]]


class CStyleCommentsParser(object):
    def p_comment(self, p):
        """comment : HASHCOMMENT
                   | CCOMMENT
        """
        p[0] = ['comment', p[1]]


class IncludesParser(object):
    def p_include(self, p):
        """include : INCLUDE
        """
        p[0] = ['include', p[1]]


class ApacheIncludesParser(object):
    def p_apacheinclude(self, p):
        """include : INCLUDE
                   | APACHEINCLUDE
        """
        p[0] = ['include', p[1]]


class BaseApacheConfigParser(object):

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

    def p_statement(self, p):
        """statement : OPTION_AND_VALUE
        """
        p[0] = ['statement', p[1][0], p[1][1]]

        if self.options.get('lowercasenames'):
            p[0][1] = p[0][1].lower()

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
                    | contents include
                    | contents block
                    | statements
                    | comment
                    | include
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

        if self.options.get('lowercasenames'):
            for tag in (1, 3):
                p[0][tag] = p[0][tag].lower()

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


def make_parser(**options):

    parser_class = BaseApacheConfigParser

    if options.get('ccomments', True):
        parser_class = type('ApacheConfigParser',
                            (parser_class, CStyleCommentsParser),
                            {'options': options})
    else:
        parser_class = type('ApacheConfigParser',
                            (parser_class, HashCommentsParser),
                            {'options': options})

    if options.get('useapacheinclude', True):
        parser_class = type('ApacheConfigParser',
                            (parser_class, ApacheIncludesParser),
                            {'options': options})
    else:
        parser_class = type('ApacheConfigParser',
                            (parser_class, IncludesParser),
                            {'options': options})


    return parser_class
