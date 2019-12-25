#
# This file is part of apacheconfig software.
#
# Copyright (c) 2018-2019, Ilya Etingof <etingof@gmail.com>
# License: https://github.com/etingof/apacheconfig/LICENSE.rst
#
from __future__ import unicode_literals

import logging
import ply.yacc as yacc
import six

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
           includeoptional : INCLUDE
        """
        # lexer returns ['<<', include, whitespace, value, '>>']
        if self._preserve_whitespace:
            p[0] = ['include'] + p[1]
        else:
            p[0] = ['include', p[1][3]]


class ApacheIncludesParser(object):
    def p_apacheinclude(self, p):
        """include : INCLUDE
                   | APACHEINCLUDE
        """
        # lexer could return ['<<', include, whitespace, value, '>>'] or
        #                    [include, whitespace, value]
        if self._preserve_whitespace:
            p[0] = ['include'] + list(p[1])
            return
        filename_index = 2
        if p[1][0] == '<<':
            filename_index = 3
        p[0] = ['include', p[1][filename_index]]

    def p_includeoptional(self, p):
        """includeoptional : APACHEINCLUDEOPTIONAL
        """
        # lexer returns [includeoptional, whitespace, value]
        if self._preserve_whitespace:
            p[0] = ['includeoptional'] + list(p[1])
        else:
            p[0] = ['includeoptional', p[1][2]]


class BaseApacheConfigParser(object):

    def __init__(self, lexer, start='config', tempdir=None, debug=False):
        self._lexer = lexer
        self.tokens = lexer.tokens  # parser needs this implicitly
        self._tempdir = tempdir
        self._debug = debug
        self._start = start
        self._preserve_whitespace = self.options.get('preservewhitespace',
                                                     False)
        self.engine = None
        self.reset()

    def reset(self):
        self.engine = yacc.yacc(
            module=self,
            start=self._start,
            outputdir=self._tempdir,
            write_tables=bool(self._tempdir),
            debug=self._debug,
            debuglog=log if self._debug else yacc.NullLogger(),
            errorlog=log if self._debug else yacc.NullLogger(),
        )

    def parse(self, text):
        self.reset()
        return self.engine.parse(text)

    # PARSING RULES
    # =============

    def p_requirednewline(self, p):
        """requirednewline : NEWLINE
        """
        p[0] = p[1]

    def p_whitespace(self, p):
        """whitespace : requirednewline
                      | WHITESPACE
        """
        p[0] = p[1]

    def p_statement(self, p):
        """statement : OPTION_AND_VALUE
                     | OPTION_AND_VALUE_NOSTRIP
        """
        p[0] = ['statement']
        if self._preserve_whitespace:
            p[0] += p[1]
        else:
            if len(p[1]) > 1:
                p[0] += [p[1][0], p[1][2]]
            else:
                p[0] += p[1]

        if self.options.get('lowercasenames'):
            p[0][1] = p[0][1].lower()

    # Note: item vs comment
    # ---------------------
    # `item` and `comment` are differentiated since there can be in-line
    # comments. Comments do not necessarily need a newline to separate it
    # from a previous item, but an item needs a newline to
    # separate it from a previous item or comment.

    def p_item(self, p):
        """item : statement
                | include
                | includeoptional
                | block
        """
        p[0] = p[1]

    def p_startitem(self, p):
        """startitem : whitespace item
                     | whitespace comment
                     | item
                     | comment
        """
        if len(p) == 3:
            if self._preserve_whitespace:
                item = p[2]
                p[0] = [item[0]] + [p[1]] + item[1:]
            else:
                p[0] = p[2]
        else:
            p[0] = p[1]

    def p_miditem(self, p):
        """miditem : requirednewline item
                   | whitespace comment
                   | comment
        """
        if len(p) == 3:
            if self._preserve_whitespace:
                item = p[2]
                p[0] = [item[0]] + [p[1]] + item[1:]
            else:
                p[0] = p[2]
        else:
            p[0] = p[1:][0]

    def p_contents(self, p):
        """contents : contents whitespace
                    | contents miditem
                    | whitespace
                    | startitem
        """
        n = len(p)
        if n == 3:
            if isinstance(p[2], six.text_type) and p[2].isspace():
                # contents whitespace
                if self._preserve_whitespace:
                    p[0] = p[1] + [p[2]]
                else:
                    p[0] = p[1]
            else:
                # contents miditem
                p[0] = p[1] + [p[2]]
        else:
            if (not self._preserve_whitespace and
               isinstance(p[1], six.text_type) and p[1].isspace()):
                # whitespace
                # (if contents only consists of whitespace)
                p[0] = []
            else:
                # startitem
                p[0] = ['contents', p[1]]

    def p_block(self, p):
        """block : OPEN_TAG contents CLOSE_TAG
                 | OPEN_CLOSE_TAG
        """
        n = len(p)
        if n == 4:
            if isinstance(p[2], six.text_type) and p[2].isspace():
                p[2] = []
            p[0] = ['block', p[1], p[2], p[3]]
        else:
            p[0] = ['block', p[1], [], "".join(p[1])]

        if self.options.get('lowercasenames'):
            p[0][1] = tuple(x.lower() for x in p[0][1])
            p[0][3] = p[0][3].lower()

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
        raise ApacheConfigError("Parser error at '%s'" % p.value
                                if p else'Unexpected EOF')


def make_parser(**options):

    parser_class = BaseApacheConfigParser

    if options.get('ccomments', True):
        parser_class = type(str('ApacheConfigParser'),
                            (parser_class, CStyleCommentsParser),
                            {'options': options})
    else:
        parser_class = type(str('ApacheConfigParser'),
                            (parser_class, HashCommentsParser),
                            {'options': options})

    if options.get('useapacheinclude', True):
        parser_class = type(str('ApacheConfigParser'),
                            (parser_class, ApacheIncludesParser),
                            {'options': options})
    else:
        parser_class = type(str('ApacheConfigParser'),
                            (parser_class, IncludesParser),
                            {'options': options})

    return parser_class
