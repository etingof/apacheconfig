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
class Node(object):
    """Generic class containing data that represents a node in the config AST.
    """

    @abc.abstractmethod
    def dump(self):
        """Dumps the contents of this node to a raw string.

        :returns: Contents of this node as it would appear in a config file.
        :rtype: `str`
        """

    @abc.abstractproperty
    def ast_node_type(self):
        """Returns object typestring as defined by the apacheconfig parser.

        :returns: a string containing literal preceding or trailing whitespace.
        :rtype: `str`
        """

    @abc.abstractproperty
    def whitespace(self):
        """Returns preceding or trailing whitespace for this node.
        :returns: a string containing literal preceding or trailing whitespace.
        :rtype: `str`
       """

    @abc.abstractmethod
    @whitespace.setter
    def whitespace(self, value):
        """Set preceding or trailing whitespace for this node.

        :param str value: value to set whitespace to.
        """


class ItemNode(Node):
    """Creates object containing data for a comment or option-value directive.

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

    @property
    def ast_node_type(self):
        """Returns object typestring as defined by the apacheconfig parser.

        :returns: The typestring (as defined by the apacheconfig parser) for
                  this node. The possible values for this are ``comment``,
                  ``statement``, ``include``, ``includeoptional``.
        :rtype: `str`
        """
        return self._type

    @property
    def whitespace(self):
        """Returns preceding whitespace for this node.

        For example::

            ItemNode('\\n  option value').whitespace => "\\n  "
            ItemNode('option value').whitespace => ""
            ItemNode('\\n  # comment').whitespace => "\\n  "

        :returns: a string containing literal preceding or trailing whitespace
                  information for this node.
        :rtype: `str`
        """
        return self._whitespace

    @whitespace.setter
    def whitespace(self, value):
        """Set preceding whitespace for this node.

        :param str value: value to set this node's preceding whitespace.
        """
        self._whitespace = value

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
        """Returns the name of this node.

        Returns the first non-whitespace token in the directive.
        Cannot be written. For comments, is the entire comment.

        :returns: The name of this node.
        :rtype: `str`
        """
        return self._raw[0]

    @property
    def has_value(self):
        """Returns whether value exists.

        ``ItemNode`` objects don't have to have a value, like option/value
        directives with no value, or comments.

        :returns: True if this ``ItemNode`` has a value.
        :rtype: `bool`
        """
        return len(self._raw) > 1

    @property
    def value(self):
        """Returns the value of this item.

        The "value" is anything but the name. Can be overwritten.

        :returns: The value of this node.
        :rtype: `str`
        """
        if not self.has_value:
            return None
        return self._raw[-1]

    @value.setter
    def value(self, value):
        """Sets for the value of this item.

        :param str value: string to set new value to.

          .. todo:: (sydneyli) convert `value` to quotedstring when quoted
        """
        if not self.has_value:
            self._raw = self._raw + (" ", value,)
        self._raw = self._raw[0:-1] + (value,)

    def dump(self):
        return (self.whitespace +
                "".join([_restore_original(word) for word in self._raw]))

    def __str__(self):
        return ("%s(%s)"
                % (self.__class__.__name__,
                   str([self._type] +
                       [_restore_original(word) for word in self._raw])))


def _create_apache_parser(options={}, start='contents'):
    """Creates a ``ApacheConfigParser`` with default options that are expected
    by Apache's native parser.

    Overrides apacheconfig options ``preservewhitespace``,
    ``disableemptyelementtags``, and ``multilinehashcomments`` to ``True``.

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
