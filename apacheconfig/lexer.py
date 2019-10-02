#
# This file is part of apacheconfig software.
#
# Copyright (c) 2018-2019, Ilya Etingof <etingof@gmail.com>
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

    states = (('hashcomment', 'exclusive'),)

    def t_hashcomment_body(self, t):
        r'.*(\\\n)$'

    def t_hashcomment_error(self, t):
        raise ApacheConfigError("Illegal character '%s' in hash comment"
                                % t.value[0])

    def t_hashcomment_end(self, t):
        r'.+$'
        t.value = t.lexer.lexdata[t.lexer.code_start:
                                  t.lexer.lexpos + len(t.value)]
        t.type = "HASHCOMMENT"
        t.lexer.lineno += t.value.count('\n')
        return t

    def t_HASHCOMMENT(self, t):
        r'(?<!\\)\#[^\n\r]*'

        if self.options.get('multilinehashcomments'):
            if t.value.endswith('\\'):
                t.lexer.code_start = t.lexer.lexpos - len(t.value)
                t.lexer.begin('hashcomment')
                return
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
            t.value = t.lexer.lexdata[t.lexer.code_start:
                                      t.lexer.lexpos + 1 - 3]
            t.type = "CCOMMENT"
            t.lexer.lineno += t.value.count('\n')
            t.lexer.begin('INITIAL')
            return t

    def t_ccomment_body(self, t):
        r'.+?'

    def t_ccomment_error(self, t):
        raise ApacheConfigError("Illegal character '%s' in C-style comment"
                                % t.value[0])


class ApacheIncludesLexer(object):
    tokens = (
        'APACHEINCLUDE',
        'APACHEINCLUDEOPTIONAL'
    )

    states = ()

    def t_APACHEINCLUDE(self, t):
        r'(?i)include[\t ]+[^\n\r]+'
        include, whitespace, value = re.split(r'([ \t]+)', t.value, maxsplit=1)
        t.value = include, whitespace, value
        return t

    def t_APACHEINCLUDEOPTIONAL(self, t):
        r'(?i)includeoptional[\t ]+[^\n\r]+'
        include, whitespace, value = re.split(r'([ \t]+)', t.value, maxsplit=1)
        t.value = include, whitespace, value
        return t


class BaseApacheConfigLexer(object):

    tokens = (
        'INCLUDE',
        'OPEN_TAG',
        'CLOSE_TAG',
        'OPEN_CLOSE_TAG',
        'OPTION_AND_VALUE',
        'OPTION_AND_VALUE_NOSTRIP',
        'WHITESPACE',
        'NEWLINE',
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
        r'<<(?i)include[\t ]+[^\n\r\t]+>>'
        include, whitespace, value = re.split(r'([ \t]+)',
                                              t.value[2:-2], maxsplit=1)
        t.value = '<<', include, whitespace, value, '>>'
        return t

    def t_CLOSE_TAG(self, t):
        r'</[^\n\r]+>'
        t.value = t.value[2:-1]
        return t

    def t_OPEN_CLOSE_TAG(self, t):
        r'<[^\n\r/]*?[^\n\r/ ]/>'
        t.value = t.value[1:-2]
        return t

    def t_OPEN_TAG(self, t):
        r'<[^\n\r]+>'
        t.value = t.value[1:-1]
        return t

    @staticmethod
    def _parse_option_value(token, lineno):
        if not re.match(r'.*?(?:\s|=|\\\s)+', token):
            return token, None, None
        option, middle, value = re.split(r'((?:\s|=|\\\s)+)', token,
                                         maxsplit=1)
        if not option:
            raise ApacheConfigError(
                'Syntax error in option-value pair %s on line '
                '%d' % (token, lineno))
        if value:
            stripped = value.strip()
            if stripped[0] == '"' and stripped[-1] == '"':
                value = DoubleQuotedString(stripped[1:-1])
            if stripped[0] == "'" and stripped[-1] == "'":
                value = SingleQuotedString(stripped[1:-1])
        return option, middle, value

    def _pre_parse_value(self, option, value):
        try:
            pre_parse_value = self.options['plug']['pre_parse_value']
            return pre_parse_value(option, value)

        except KeyError:
            return True, option, value

    def _lex_option(self, t):
        if t.value.endswith('\\'):
            t.lexer.multiline_newline_seen = False
            t.lexer.code_start = t.lexer.lexpos - len(t.value)
            t.lexer.begin('multiline')
            return

        lineno = len(re.findall(r'\r\n|\n|\r', t.value))

        option, whitespace, value = self._parse_option_value(t.value, t.lineno)
        if not value:
            t.value = (option,)
            return t

        process, option, value = self._pre_parse_value(option, value)
        if not process:
            return

        if value.startswith('<<'):
            t.lexer.heredoc_anchor = value[2:].strip()
            t.lexer.heredoc_option = option
            t.lexer.heredoc_whitespace = whitespace
            t.lexer.code_start = t.lexer.lexpos + 1
            t.lexer.begin('heredoc')
            return

        t.value = option, whitespace, value

        t.lexer.lineno += lineno

        return t

    def t_multiline_OPTION_AND_VALUE(self, t):
        r'[^\r\n]+'
        t.lexer.multiline_newline_seen = False

        if t.value.endswith('\\'):
            return

        t.type = "OPTION_AND_VALUE"
        t.lexer.begin('INITIAL')

        value = t.lexer.lexdata[t.lexer.code_start:t.lexer.lexpos + 1]
        value = self._remove_trailing_whitespace(value)
        t.lexer.lexpos = t.lexer.code_start + len(value)
        t.lexer.lineno += len(re.findall(r'\r\n|\n|\r', value))

        option, whitespace, value = self._parse_option_value(value, t.lineno)

        process, option, value = self._pre_parse_value(option, value)
        if not process:
            return

        t.value = option, whitespace, value

        return t

    def t_multiline_NEWLINE(self, t):
        r'\r\n|\n|\r'
        if t.lexer.multiline_newline_seen:
            return self.t_multiline_OPTION_AND_VALUE(t)
        t.lexer.multiline_newline_seen = True

    def t_multiline_error(self, t):
        raise ApacheConfigError(
            "Illegal character '%s' in multi-line text on line "
            "%d" % (t.value[0], t.lineno))

    def _remove_trailing_whitespace(self, value):
        # if stripped_value ends with an odd number of backslashes, the first
        # trailing whitespace character was escaped, should be in `value`
        def trailing_escape(s):
            return (len(s) - len(s.rstrip('\\'))) % 2 == 1
        value = value.rstrip()
        while trailing_escape(value):
            value = value[:-1].rstrip()
        return value

    def t_heredoc_OPTION_AND_VALUE(self, t):
        r'[^\r\n]+'
        if t.value.lstrip() != t.lexer.heredoc_anchor:
            return

        t.type = "OPTION_AND_VALUE"
        t.lexer.begin('INITIAL')

        value = t.lexer.lexdata[t.lexer.code_start:
                                t.lexer.lexpos - len(t.lexer.heredoc_anchor)]
        value = self._remove_trailing_whitespace(value)

        t.lexer.lineno += len(re.findall(r'\r\n|\n|\r', t.value))

        t.value = t.lexer.heredoc_option, t.lexer.heredoc_whitespace, value

        return t

    def t_heredoc_NEWLINE(self, t):
        r'\r\n|\n|\r'
        t.lexer.lineno += 1

    def t_heredoc_error(self, t):
        raise ApacheConfigError(
            "Illegal character '%s' in here-document text on line "
            "%d" % (t.value[0], t.lineno))

    def t_NEWLINE(self, t):
        r'[ \t]*((\r\n|\n|\r|\\)[\t ]*)+'
        if t.value != '\\':
            t.lexer.lineno += 1
        return t

    def t_WHITESPACE(self, t):
        r'[ \t]+'
        return t

    def t_error(self, t):
        raise ApacheConfigError(
            "Illegal character '%s' on line %d" % (t.value[0], t.lineno))


class OptionLexer(BaseApacheConfigLexer):
    def t_OPTION_AND_VALUE(self, t):
        r'[^ \n\r\t=#]+([ \t=]+(?:\\#|[^ \t\r\n#])+)*'
        # Regex above matches (text, (spaces, text)*) where text
        # can include escaped hashes but not regular ones.
        return self._lex_option(t)


class NoStripLexer(BaseApacheConfigLexer):
    def t_OPTION_AND_VALUE_NOSTRIP(self, t):
        r'[^ \n\r\t=#]+[ \t=]+(?:\\#|[^\r\n#])+'
        return self._lex_option(t)


def make_lexer(**options):
    lexer_class = OptionLexer
    if options.get('nostripvalues'):
        lexer_class = NoStripLexer

    lexer_class = type('ApacheConfigLexer',
                       (lexer_class, HashCommentsLexer),
                       {'tokens': lexer_class.tokens +
                        HashCommentsLexer.tokens,
                        'states': lexer_class.states +
                        HashCommentsLexer.states,
                        'options': options})

    if options.get('ccomments', True):
        lexer_class = type('ApacheConfigLexer',
                           (lexer_class, CStyleCommentsLexer),
                           {'tokens': lexer_class.tokens +
                            CStyleCommentsLexer.tokens,
                            'states': lexer_class.states +
                            CStyleCommentsLexer.states,
                            'options': options})

    if options.get('useapacheinclude', True):
        lexer_class = type('ApacheConfigLexer',
                           (lexer_class, ApacheIncludesLexer),
                           {'tokens': lexer_class.tokens +
                            ApacheIncludesLexer.tokens,
                            'states': lexer_class.states +
                            ApacheIncludesLexer.states,
                            'options': options})

    return lexer_class
