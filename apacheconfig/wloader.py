#
# This file is part of apacheconfig software.
#
# Copyright (c) 2018-2019, Ilya Etingof <etingof@gmail.com>
# License: https://github.com/etingof/apacheconfig/LICENSE.rst
#
from apacheconfig import make_parser
from apacheconfig import make_lexer

import abc
import six


def _restore_original(word):
    """If the `word` is a Quoted string, restores it to original.
    """
    if getattr(word, 'is_single_quoted', False):
        return "'%s'" % word
    if getattr(word, 'is_double_quoted', False):
        return '"%s"' % word
    return word


@six.add_metaclass(abc.ABCMeta)
class Node():
    """Generic class containing data that represents a node in the config AST.
    """

    @abc.abstractmethod
    def __str__(self):
        pass

    @property
    def parser_type(self):
        """A typestring as defined by the apacheconfig parser.

        A single *Node class can have multiple possible values for this. For
        instance, ItemNode is a generic representation of any single directive
        but has a couple different possible `type`s, including `comment`,
        `statement`, and `include`-- depending on which the caller may
        decide to treat ItemNode differently.
        """
        if self._type is None:
            raise NotImplementedError()
        return self._type

    @property
    def whitespace(self):
        """A string representing literal trailing or preceding whitespace
        for this node.

        Each Item or BlockNode keeps track of the whitespace preceding it.
        For the first element in the configuration file, there could be no
        whitespace preceding it at all, in which case this should return the
        empty string.

        ContentsNode is special in that it keeps track of the trailing white-
        space.

        Some examples:
          ItemNode('\n  option value').whitespace => "\n  "
          ItemNode('\n  # comment').whitespace => "\n  "
          BlockNode('\n  <a>\n</a>').whitespace => "\n  "
          ContentsNode('\n  option value # comment\n').whitespace => "\n"
        """
        if self._whitespace is None:
            raise NotImplementedError()
        return self._whitespace

    @whitespace.setter
    def whitespace(self, value):
        if self._whitespace is None:
            raise NotImplementedError()
        self._whitespace = value


class ItemNode(Node):
    """Contains data for a comment or directive (or option-value store).

    Also manages any preceding whitespace. Can represent a key/value option,
    a comment, or an include/includeoptional directive.

    Construct this using raw AST data from parser. Generally, block data looks
    like:
        ['block', <open tag>, <contents object>
    Examples of what raw AST data might look like for an ItemNode:
        ['statement', 'option', ' ', 'value']
        ['include', 'include', ' ', 'relative/path/*']
        ['statement', '\n  ', 'option', ' = ', 'value']
        ['comment', '# here is a comment']
        ['comment', '\n  ', '# here is a comment']

    Properties:
        value: getter & setter for the final element in the raw AST. For
               includes, this would be the path for include directives; for
               comments, it's the comment body, and for key/value directives,
               it's the value.
        name:  getter only. Retrieves the first non-whitespace element in the
               raw AST.
    """

    def __init__(self, raw):
        """Initializes ItemNode with raw data from AST

        Args:
            raw: list from parser module's AST.
        """
        self._type = raw[0]
        self._raw = tuple(raw[1:])
        self._whitespace = ""
        if len(raw) > 1 and raw[1].isspace():
            self._whitespace = raw[1]
            self._raw = tuple(raw[2:])

    @property
    def name(self):
        """Getter for the first non-whitespace token, semantically the "name"
        of this directive.

        Useful for retrieving the key if this is a key/value directive.
        """
        return self._raw[0]

    def has_value(self):
        return len(self._raw) > 1

    @property
    def value(self):
        """Getter for the last token, semantically the "value" of this item.
        """
        if not self.has_value():
            return None
        return self._raw[-1]

    @value.setter
    def value(self, value):
        """Setter for the value of this item.
        TODO(sydli): convert `value` to quotedstring automagically if quoted
        """
        if not self.has_value():
            self._raw = self._raw + (" ", value,)
        self._raw = self._raw[0:-1] + (value,)

    def __str__(self):
        return (self.whitespace +
                "".join([_restore_original(word) for word in self._raw]))

    def __repr__(self):
        return ("%s(%s)"
                % (self.__class__.__name__,
                   str([self._type] +
                       [_restore_original(word) for word in self._raw])))


def _create_parser(options={}, start='contents'):
    options['preservewhitespace'] = True
    options['disableemptyelementtags'] = True
    options['multilinehashcomments'] = True
    ApacheConfigLexer = make_lexer(**options)
    ApacheConfigParser = make_parser(**options)
    return ApacheConfigParser(ApacheConfigLexer(), start=start)


def parse_item(raw_str, options={}):
    parser = _create_parser(options, start='startitem')
    return ItemNode(parser.parse(raw_str))
