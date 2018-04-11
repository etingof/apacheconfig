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


class SingleQuotedString(str):
    is_single_quoted = True


class DoubleQuotedString(str):
    is_double_quoted = True


class HashCommentsLexer(object):
    tokens = (
        'HASHCOMMENT',
    )

    states = ()

    def t_HASHCOMMENT(self, t):
        r'(?<!\\)\#[^\n\r]*'
        t.value = t.value[1:]
        return t


class CStyleCommentsLexer(object):
    tokens = (
        'CCOMMENT',
    )

    states = (
        ('ccomment', 'exclusive'),
    )

    def t_CCOMMENT(self, t):
        r'\/\*'
        t.lexer.code_start = t.lexer.lexpos
        t.lexer.ccomment_level = 1  # Initial comment level
        t.lexer.begin('ccomment')

    def t_ccomment_open(self, t):
        r'\/\*'
        t.lexer.ccomment_level += 1

    def t_ccomment_close(self, t):
        r'\*\/'
        t.lexer.ccomment_level -= 1

        if t.lexer.ccomment_level == 0:
            t.value = t.lexer.lexdata[t.lexer.code_start:t.lexer.lexpos + 1 - 3]
            t.type = "CCOMMENT"
            t.lexer.lineno += t.value.count('\n')
            t.lexer.begin('INITIAL')
            return t

    def t_ccomment_body(self, t):
        r'.+?'

    def t_ccomment_error(self, t):
        raise ApacheConfigError("Illegal character '%s' in C-style comment" % t.value[0])


class ApacheIncludesLexer(object):
    tokens = (
        'APACHEINCLUDE',
    )

    states = ()

    def t_APACHEINCLUDE(self, t):
        r'include[\t ]+[^\n\r]+'
        t.value = t.value.split(None, 1)[1]
        return t


class BaseApacheConfigLexer(object):

    tokens = (
        'INCLUDE',
        'OPEN_TAG',
        'CLOSE_TAG',
        'OPEN_CLOSE_TAG',
        'OPTION_AND_VALUE',
    )

    states = (
        ('multiline', 'exclusive'),
        ('heredoc', 'exclusive'),
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

    def t_INCLUDE(self, t):
        r'<<include[\t ]+[^\n\r\t]+>>'
        t.value = t.value[2:-2].split(None, 1)[1]
        return t

    def t_CLOSE_TAG(self, t):
        r'</[^\n\r]+>'
        t.value = t.value[2:-1]
        return t

    def t_OPEN_CLOSE_TAG(self, t):
        r'<[^\n\r/]+/>'
        t.value = t.value[1:-2]
        return t

    def t_OPEN_TAG(self, t):
        r'<[^\n\r]+>'
        t.value = t.value[1:-1]
        return t

    @staticmethod
    def _parse_option_value(token):
        if not re.match(r'.*?[ \n\r\t=]+', token):
            raise ApacheConfigError('Syntax error in option-value pair %s' % token)
        option, value = re.split(r'[ \n\r\t=]+', token, maxsplit=1)
        if not option or not value:
            raise ApacheConfigError('Syntax error in option-value pair %s' % token)
        if value[0] == '"' and value[-1] == '"':
            value = DoubleQuotedString(value[1:-1])
        if value[0] == "'" and value[-1] == "'":
            value = SingleQuotedString(value[1:-1])
        if '#' in value:
            value = value.replace('\\#', '#')
        return option, value

    def _pre_parse_value(self, option, value):
        try:
            pre_parse_value = self.options['plug']['pre_parse_value']
            return pre_parse_value(option, value)

        except KeyError:
            return True, option, value

    def t_OPTION_AND_VALUE(self, t):
        r'[^ \n\r\t=]+[ \n\r\t=]+[^\r\n]+'
        if t.value.endswith('\\'):
            t.lexer.code_start = t.lexer.lexpos - len(t.value)
            t.lexer.begin('multiline')
            return

        lineno = len(re.findall(r'\r\n|\n|\r', t.value))

        option, value = self._parse_option_value(t.value)

        process, option, value = self._pre_parse_value(option, value)
        if not process:
            return

        if value.startswith('<<'):
            t.lexer.heredoc_anchor = value[2:].strip()
            t.lexer.heredoc_option = option
            t.lexer.code_start = t.lexer.lexpos
            t.lexer.begin('heredoc')
            return

        t.value = option, value

        t.lexer.lineno += lineno

        return t

    def t_multiline_OPTION_AND_VALUE(self, t):
        r'[^\r\n]+'
        if t.value.endswith('\\'):
            return

        t.type = "OPTION_AND_VALUE"
        t.lexer.begin('INITIAL')

        value = t.lexer.lexdata[t.lexer.code_start:t.lexer.lexpos + 1]
        t.lexer.lineno += len(re.findall(r'\r\n|\n|\r', value))
        value = value.replace('\\\n', '').replace('\r', '').replace('\n', '')

        option, value = self._parse_option_value(value)

        process, option, value = self._pre_parse_value(option, value)
        if not process:
            return

        t.value = option, value

        return t

    def t_multiline_NEWLINE(self, t):
        r'\r\n|\n|\r'
        t.lexer.lineno += 1

    def t_multiline_error(self, t):
        raise ApacheConfigError("Illegal character '%s' in multiline text" % t.value[0])

    def t_heredoc_OPTION_AND_VALUE(self, t):
        r'[^\r\n]+'
        if t.value != t.lexer.heredoc_anchor:
            return

        t.type = "OPTION_AND_VALUE"
        t.lexer.begin('INITIAL')

        value = t.lexer.lexdata[t.lexer.code_start + 1:t.lexer.lexpos - len(t.lexer.heredoc_anchor)]

        t.lexer.lineno += len(re.findall(r'\r\n|\n|\r', t.value))

        t.value = t.lexer.heredoc_option, value

        return t

    def t_heredoc_NEWLINE(self, t):
        r'\r\n|\n|\r'
        t.lexer.lineno += 1

    def t_heredoc_error(self, t):
        raise ApacheConfigError("Illegal character '%s' in here-document text" % t.value[0])

    def t_WHITESPACE(self, t):
        r'[ \t]+'

    def t_NEWLINE(self, t):
        r'\r\n|\n|\r'
        t.lexer.lineno += 1

    def t_error(self, t):
        raise ApacheConfigError("Illegal character '%s'" % t.value[0])


def make_lexer(**options):

    lexer_class = BaseApacheConfigLexer

    lexer_class = type('ApacheConfigLexer',
                       (lexer_class, HashCommentsLexer),
                       {'tokens': lexer_class.tokens + HashCommentsLexer.tokens,
                        'states': lexer_class.states + HashCommentsLexer.states,
                        'options': options})

    if options.get('ccomments', True):
        lexer_class = type('ApacheConfigLexer',
                           (lexer_class, CStyleCommentsLexer),
                           {'tokens': lexer_class.tokens + CStyleCommentsLexer.tokens,
                            'states': lexer_class.states + CStyleCommentsLexer.states,
                            'options': options})

    if options.get('useapacheinclude', True):
        lexer_class = type('ApacheConfigLexer',
                           (lexer_class, ApacheIncludesLexer),
                           {'tokens': lexer_class.tokens + ApacheIncludesLexer.tokens,
                            'states': lexer_class.states + ApacheIncludesLexer.states,
                            'options': options})

    return lexer_class
