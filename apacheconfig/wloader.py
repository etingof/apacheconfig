#
# This file is part of apacheconfig software.
#
# Copyright (c) 2018-2019, Ilya Etingof <etingof@gmail.com>
# License: https://github.com/etingof/apacheconfig/LICENSE.rst
#
import abc
import six

from apacheconfig import make_parser
from apacheconfig import make_lexer


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
        """Writes this node to a raw string. To get more metadata about the
        object, use ``repr``.
        """
        pass

    @abc.abstractmethod
    def __repr__(self):
        """Returns a string containing object metadata."""
        pass

    @property
    def parser_type(self):
        """A typestring as defined by the apacheconfig parser.

        The possible values for this are:

        :class:`apacheconfig.ItemNode`: ``comment``, ``statement``,
        ``include``, ``includeoptional``

        :returns: The typestring (as defined by the apacheconfig parser) for
                  this node.
        :rtype: `str`
        """
        if self._type is None:
            raise NotImplementedError()
        return self._type

    @property
    def whitespace(self):
        """A string representing literal trailing or preceding whitespace
        for this node. Can be overwritten.

        Each ``ItemNode`` or ``BlockNode`` keeps track of the whitespace
        preceding it. For the first element in the configuration file, there
        could be no whitespace preceding it at all, in which case this should
        return the empty string.

        ContentsNode is special in that it keeps track of the *trailing*
        whitespace. For example::

            ItemNode('\\n  option value').whitespace => "\\n  "
            ItemNode('\\n  # comment').whitespace => "\\n  "
            BlockNode('\\n  <a>\\n</a>').whitespace => "\\n  "
            ContentsNode('\\n  option value # comment\\n').whitespace => "\\n"

        :returns: a string containing literal preceding or trailing whitespace
                  information for this node.
        :rtype: `str`
       """
        if self._whitespace is None:
            raise NotImplementedError()
        return self._whitespace

    @whitespace.setter
    def whitespace(self, value):
        """A string representing literal trailing or preceding whitespace
        for this node. Trailing for ``Contents``, preceding for ``Item`` or
        ``Block``.

        :param str value: whitespace string to set this node's whitespace.
        """
        if self._whitespace is None:
            raise NotImplementedError()
        self._whitespace = value


class ItemNode(Node):
    """Contains data for a comment or option-value directive.

    Also manages any preceding whitespace. Can represent a key/value option,
    a comment, or an include/includeoptional directive.

    Examples of what ItemNode fields might look like for different directives::

        "option"
            name: "option", value: None, whitespace: ""
        "include relative/path/*"
            name: "include", value: "relative/path/*", whitespace: ""
        "\\n  option = value"
            name: "option", value: "value", whitespace: "\\n  "
        "# here is a comment"
            name: "# here is a comment", value: None, whitespace: ""
        "\\n  # here is a comment"
            name: "# here is a comment", value: None, whitespace: "\\n  "

    To construct from a raw string, use the `parse` constructor. The regular
    constructor receives data from the internal apacheconfig parser.

    :param list raw: Raw data returned from ``apacheconfig.parser``.
    """

    def __init__(self, raw, options={}):
        self._type = raw[0]
        self._raw = tuple(raw[1:])
        self._whitespace = ""
        if len(raw) > 1 and raw[1].isspace():
            self._whitespace = raw[1]
            self._raw = tuple(raw[2:])

    @staticmethod
    def parse(raw_str, options={}, parser=None):
        """Constructs an ItemNode by parsing it from a raw string.

        :param dict options: (optional) Additional options to pass to the
                             created parser. Ignored if another ``parser`` is
                             supplied.
        :param parser: (optional) To re-use an existing parser. If ``None``,
                       creates a new one.
        :type parser: :class:`apacheconfig.ApacheConfigParser`

        :returns: an ItemNode containing metadata parsed from ``raw_str``.
        :rtype: :class:`apacheconfig.ItemNode`
        """
        if not parser:
            parser = _create_apache_parser(options, start='startitem')
        return ItemNode(parser.parse(raw_str))

    @property
    def name(self):
        """The first non-whitespace token, semantically the "name" of this
        directive. Cannot be written. For comments, is the entire comment.

        :returns: The name of this node.
        :rtype: `str`
        """
        return self._raw[0]

    def has_value(self):
        """Returns whether value exists. ``ItemNode`` objects don't have to
        have a value, like option/value directives with no value, or comments.

        :returns: True if this ``ItemNode`` has a value.
        :rtype: `bool`
        """
        return len(self._raw) > 1

    @property
    def value(self):
        """Everything but the name, semantically the "value" of this item.
        Can be overwritten.

        :returns: The value of this node.
        :rtype: `str`
        """
        if not self.has_value():
            return None
        return self._raw[-1]

    @value.setter
    def value(self, value):
        """Setter for the value of this item.

        :param str value: string to set new value to.

          .. todo:: (sydneyli) convert `value` to quotedstring when quoted
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


def _create_apache_parser(options={}, start='contents'):
    """Creates a ``ApacheConfigParser`` with default options that are expected
    by Apache's native parser, to enable the writable loader to work.

    Overrides options ``preservewhitespace``, ``disableemptyelementtags``, and
    ``multilinehashcomments`` to ``True``.

    :param dict options: Additional parameters to pass.
    :param str start: Which parsing token, as defined by the apacheconfig
                      parser, to expect at the root of strings. This is an
                      internal flag and shouldn't need to be used.
    """
    options['preservewhitespace'] = True
    options['disableemptyelementtags'] = True
    options['multilinehashcomments'] = True
    ApacheConfigLexer = make_lexer(**options)
    ApacheConfigParser = make_parser(**options)
    return ApacheConfigParser(ApacheConfigLexer(), start=start)
