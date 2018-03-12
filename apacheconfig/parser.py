#
# This file is part of apacheconfig software.
#
# Copyright (c) 2018, Ilya Etingof <etingof@gmail.com>
# License: https://github.com/etingof/apacheconfig/LICENSE
#
import functools

from pyparsing import *

__all__ = ['Parser']

WHITE = White(ws=' \t')

# For tags that have an argument in the form of
# a conditional expression. The reason this is done
# is so that a tag with the ">" operator in the
# arguments will parse correctly.
OPERAND = Word(alphanums + "." + '"' + '/-' + "*:^_![]?$%@)(#=`" + '\\')
OPERATOR = oneOf(["<=", ">=", "==", "!=", "<", ">", "~"], useRegex=False)
EXPRESSION_TAG = OPERAND + Suppress(ZeroOrMore(WHITE)) + OPERATOR + Suppress(ZeroOrMore(WHITE)) + OPERAND

def handle_one_option(*args):
    pass

# LITERAL_TAG will match tags that do not have
# a conditional expression. So any other tag
# with arguments that don't contain OPERATORs
LITERAL_TAG = Suppress(ZeroOrMore(WHITE)) + OneOrMore(Word(alphanums)) + Suppress(ZeroOrMore(WHITE))

# Will match the start of any tag
OPEN_TAG = (
    Suppress(Literal("<")) +
    (LITERAL_TAG) +
    Suppress(Literal(">")) +
    Suppress(LineEnd())
)

# Will match the end of any tag
CLOSE_TAG = (
    Suppress(Literal("</")) +
    Suppress(ZeroOrMore(WHITE)) + (LITERAL_TAG) + Suppress(ZeroOrMore(WHITE)) +
    Suppress(Literal(">")) +
    Suppress(LineEnd())
)

OPTION_NAME = Word(alphanums)
OPTION_VALUE = QuotedString('"', escChar='\\') ^ Word(printables)
OPTION_AND_VALUE = Group(OPTION_NAME + Suppress(OneOrMore(WHITE | Literal('='))) + OPTION_VALUE)

OPTION_AND_VALUE_SET = (OPTION_AND_VALUE + OneOrMore(Suppress(LineEnd()) + OPTION_AND_VALUE)) | OPTION_AND_VALUE

# TODO: RegExp comments
COMMENT = Group(
    Suppress(LineStart() + ZeroOrMore(WHITE) + Literal("#")) +
    ZeroOrMore(Word(alphanums) | WHITE) +
    Suppress(LineEnd())
)

COMMENTS = (COMMENT + COMMENT) | COMMENT

BLANK_LINE = OneOrMore(Suppress(LineEnd()))

BLOCK_CONTENTS = OPTION_AND_VALUE_SET | COMMENTS | BLANK_LINE

BLOCK = (BLOCK_CONTENTS + BLOCK_CONTENTS) | BLOCK_CONTENTS

TAGGED_BLOCK_CONTENTS = OPEN_TAG + BLOCK + CLOSE_TAG | COMMENTS | BLANK_LINE

TAGGED_BLOCK = (TAGGED_BLOCK_CONTENTS + TAGGED_BLOCK_CONTENTS) | TAGGED_BLOCK_CONTENTS

BODY_CONTENTS = BLOCK | TAGGED_BLOCK

BODY = (BODY_CONTENTS + BODY_CONTENTS) | BODY_CONTENTS

CONFIGURATION = BODY

context = {1: 2}

def handle_option(context, *args):
    pass

def handle_literal_tag(context, *args):
    pass

#LITERAL_TAG.setParseAction(functools.partial(handle_option, context))

class Parser(object):

    def parse_file(self, filename):

        with open(filename) as config_file:
            return CONFIGURATION.parseString(config_file.read())
