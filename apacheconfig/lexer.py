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
        'OPTION_AND_VALUE',
        'NEWLINE',
    )

    states = (
        ('multiline', 'exclusive'),
    )

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

    @staticmethod
    def _parse_option_value(token):
        option, value = re.split(r'[ \n\r\t=]+', token, maxsplit=1)
        if value[0] == '"':
            value = value[1:]
        if value[-1] == '"':
            value = value[:-1]
        if '#' in value:
            value = value.replace('\\#', '#')
        return option, value

    def t_OPTION_AND_VALUE(self, t):
        r'[^ \n\r\t=]+[ \n\r\t=]+[^\r\n]+'
        if t.value.endswith('\\'):
            t.lexer.code_start = t.lexer.lexpos - len(t.value)
            t.lexer.begin('multiline')
            return

        t.lexer.lineno += len(re.findall(r'\r\n|\n|\r', t.value))

        t.value = self._parse_option_value(t.value)

        return t

    def t_multiline_OPTION_AND_VALUE(self, t):
        r'[^\r\n]+'
        if t.value.endswith('\\'):
            return

        t.type = "OPTION_AND_VALUE"
        t.lexer.begin('INITIAL')
        t.lexer.lineno += len(re.findall(r'\r\n|\n|\r', t.value))

        value = t.lexer.lexdata[t.lexer.code_start:t.lexer.lexpos + 1]
        value = value.replace('\\\n', '').replace('\r', '').replace('\n', '')

        t.value = self._parse_option_value(value)

        return t

    def t_multiline_NEWLINE(self, t):
        r'\r\n|\n|\r'
        t.lexer.lineno += 1

    def t_multiline_error(self, t):
        raise ApacheConfigError("Illegal character '%s' in multiline text" % t.value[0])

    def t_WHITESPACE(self, t):
        r'[ \t]+'

    def t_NEWLINE(self, t):
        r'\r\n|\n|\r'
        t.lexer.lineno += 1

    def t_error(self, t):
        raise ApacheConfigError("Illegal character '%s'" % t.value[0])
