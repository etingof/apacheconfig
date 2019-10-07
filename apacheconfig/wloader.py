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
        """Returns the contents of this node as it would appear in a config
        file.
        """

    @abc.abstractproperty
    def ast_node_type(self):
        """Returns object typestring as defined by the apacheconfig parser.
        """

    @abc.abstractproperty
    def whitespace(self):
        """Returns preceding or trailing whitespace for this node as a string.
       """

    @abc.abstractmethod
    @whitespace.setter
    def whitespace(self, value):
        """Set preceding or trailing whitespace for this node.

        Args:
            value (str): value to set whitespace to.
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

    Args:
        raw (list): Raw data returned from ``apacheconfig.parser``.
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

        Returns:
            The typestring (as defined by the apacheconfig parser) for
            this node. The possible values for this are ``"comment"``,
            ``"statement"``, ``"include"``, ``"includeoptional"``.
        """
        return self._type

    @property
    def whitespace(self):
        """Returns preceding whitespace for this node.

        For example::

            ItemNode('\\n  option value').whitespace => "\\n  "
            ItemNode('option value').whitespace => ""
            ItemNode('\\n  # comment').whitespace => "\\n  "
        """
        return self._whitespace

    @whitespace.setter
    def whitespace(self, value):
        """See base class. Operates on preceding whitespace."""
        self._whitespace = value

    @staticmethod
    def parse(raw_str, options={}, parser=None):
        """Factory for :class:`apacheconfig.ItemNode` by parsing data from a
        config string.

        Args:
            options (dict): Additional options to pass to the created parser.
                Ignored if another ``parser`` is supplied.
            parser (:class:`apacheconfig.ApacheConfigParser`): optional, to
                re-use an existing parser. If ``None``, creates a new one.
        Returns:
            :class:`apacheconfig.ItemNode` containing metadata parsed from
            ``raw_str``.
        """
        if not parser:
            parser = _create_apache_parser(options, start='startitem')
        return ItemNode(parser.parse(raw_str))

    @property
    def name(self):
        """Returns the name of this node.

        The name is the first non-whitespace token in the directive. Cannot be
        written. For comments, is the entire comment.
        """
        return self._raw[0]

    @property
    def has_value(self):
        """Returns ``true`` if this :class:`apacheconfig.ItemNode` has a value.

        ``ItemNode`` objects don't have to have a value, like option/value
        directives with no value, or comments.
        """
        return len(self._raw) > 1

    @property
    def value(self):
        """Returns the value of this item as a string.

        The "value" is anything but the name. Can be overwritten.
        """
        if not self.has_value:
            return None
        return self._raw[-1]

    @value.setter
    def value(self, value):
        """Sets for the value of this item.

        Args:
            value (str): string to set new value to.

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
    """Returns a :class:`apacheconfig.ApacheConfigParser` with default options
    that are expected by Apache's native parser.

    Overrides apacheconfig options ``preservewhitespace``,
    ``disableemptyelementtags``, and ``multilinehashcomments`` to ``True``.

    Params:
        options (dict): Additional parameters to pass.
        start (str): Which parsing token, as defined by the apacheconfig
            parser, to expect at the root of strings.
    """
    options['preservewhitespace'] = True
    options['disableemptyelementtags'] = True
    options['multilinehashcomments'] = True
    ApacheConfigLexer = make_lexer(**options)
    ApacheConfigParser = make_parser(**options)
    return ApacheConfigParser(ApacheConfigLexer(), start=start)
