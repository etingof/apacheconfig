#
# This file is part of apacheconfig software.
#
# Copyright (c) 2018, Ilya Etingof <etingof@gmail.com>
# License: https://github.com/etingof/apacheconfig/LICENSE.rst
#
import logging
import re
import ply.lex as lex

from apacheconfig.error import ApacheConfigError

log = logging.getLogger(__name__)


class ApacheConfigLexer(object):

    tokens = (
        'COMMENT',
        'OPEN_TAG',
        'CLOSE_TAG',
        'OPEN_CLOSE_TAG',
        'STRING',
        'NEWLINE',
    )

    literals = '='

    def __init__(self, tempdir=None, debug=False):
        self._tempdir = tempdir
        self._debug = debug
        self.engine = None
        self.reset()

    def reset(self):
        self.engine = lex.lex(
            module=self,
            reflags=re.DOTALL,
            outputdir=self._tempdir,
            debuglog=log if self._debug else None,
            errorlog=log if self._debug else None
        )

    def tokenize(self, text):
        self.engine.input(text)

        tokens = []

        while True:
            token = self.engine.token()
            if not token:
                break
            tokens.append(token.value)

        return tokens

    # Tokenizer rules

    def t_COMMENT(self, t):
        r'(?<!\\)\#[^\n\r]*'
        t.value = t.value[1:]
        return t

    def t_CLOSE_TAG(self, t):
        r'</[^\n\r\t]+>'
        t.value = t.value[2:-1]
        return t

    def t_OPEN_CLOSE_TAG(self, t):
        r'<[^\n\r\t/]+/>'
        t.value = t.value[1:-2]
        return t

    def t_OPEN_TAG(self, t):
        r'<[^\n\r\t]+>'
        t.value = t.value[1:-1]
        return t

    def t_STRING(self, t):
        r'\"[^\"]*\"|[a-zA-Z0-9!"#$%&()*+,.\/:;?@\[\]^_`{\\}~-]+'
        if t.value[0] == '"':
            t.value = t.value[1:-1]
        t.value = t.value.replace('\\#', '#')
        t.lexer.lineno += len(re.findall(r'\r\n|\n|\r', t.value))
        return t

    def t_WHITESPACE(self, t):
        r'[ \t]+'

    def t_NEWLINE(self, t):
        r'\r\n|\n|\r'
        t.lexer.lineno += 1

    def t_error(self, t):
        raise ApacheConfigError("Illegal character '%s'" % t.value[0])
