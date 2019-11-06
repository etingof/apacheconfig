#
# This file is part of apacheconfig software.
#
# Copyright (c) 2018-2019, Ilya Etingof <etingof@gmail.com>
# License: https://github.com/etingof/apacheconfig/LICENSE.rst
#
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
class AbstractASTNode(object):
    """Generic class containing data that represents a node in the config AST.
    """

    @abc.abstractmethod
    def dump(self):
        """Returns the contents of this node as in a config file."""

    @abc.abstractproperty
    def typestring(self):
        """Returns object typestring as defined by the apacheconfig parser."""

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


class ContentsNode(AbstractASTNode):
    """Creates object representing an ordered list of LeafASTNodes.

    Each BlockNode contains a ContentsNode, and every configuration file's
    root should be a ContentsNode. To construct from a raw string, use the
    `parse` factory function. The default __init__ constructor expects data
    from the internal apacheconfig parser.

    Args:
        raw (list): Raw data returned from ``apacheconfig.parser``.
    """
    def __init__(self, raw, parser):
        self._type = raw[0]
        self._contents = []
        self._whitespace = ""
        self._parser = parser
        for elem in raw[1:]:
            if isinstance(elem, str) and elem.isspace():
                self._whitespace = elem
            elif elem[0] == "block":
                self._contents.append(BlockNode(elem, parser))
            else:
                self._contents.append(LeafASTNode(elem))

    @classmethod
    def parse(cls, raw_str, parser):
        """Factory for :class:`apacheconfig.ListASTNode` from a config string.

        Args:
            raw_str (str): Config string to parse.
            parser (:class:`apacheconfig.ApacheConfigParser`): parser object
                to use.
        Returns:
            :class:`apacheconfig.ListASTNode` containing data parsed from
            ``raw_str``.
        """
        raw = parser.parse(raw_str)
        return cls(raw, parser)

    def add(self, index, raw_str):
        """Parses and adds child element at given index.

        Parses given string into an ASTNode object, then adds to contents at
        specified index.

        Args:
            index (int): index of contents at which to insert the node.
            raw_str (str): string to parse. The parser will automatically
                determine whether it's a :class:`apacheconfig.BlockNode` or
                :class:`apacheconfig.LeafASTNode`.

        Returns:
            The :class:`apacheconfig.Node` created from parsing ``raw_str``.
        """
        raw = self._parser.parse(raw_str)[1]
        if raw[0] == "block":
            node = BlockNode(raw, self._parser)
        else:
            node = LeafASTNode(raw)

        # If we're adding an element to the beginning of contents, the first
        # item may not have a preceding newline-- so we add one in case.
        # For instance, something like:
        #   Contents("line1\nline2").add(0, "\nline0")
        # should end up as "\nline0\nline1\nline2"
        if (len(self._contents) >= 1 and index == 0 and
            '\n' not in self._contents[0].whitespace):
            whitespace_after = self._contents[0].whitespace
            self._contents[0].whitespace = '\n' + whitespace_after
        self._contents.insert(index, node)
        return node

    def remove(self, index):
        """Removes node from supplied index.

        Args:
            index (int): index of node to remove from contents.

        Returns:
            The :class:`apacheconfig.Node` that was removed.
        """
        thing = self._contents[index]
        del self._contents[index]
        return thing

    def __len__(self):
        """Number of :class:`apacheconfig.Node` children."""
        return len(self._contents)

    def __iter__(self):
        """Iterator over :class:`apacheconfig.Node` children."""
        return iter(self._contents)

    def dump(self):
        """See base class."""
        return ("".join([item.dump() for item in self._contents])
                + self.whitespace)

    @property
    def typestring(self):
        """See base class.

        Can only return ``"contents"`` for :class:`apacheconfig.ContentsNode`.
        """
        return self._type

    @property
    def whitespace(self):
        """Returns trailing whitespace in contents.

        For instance, the following valid "contents" configuration::

            \\tkey value # comment\\n

        will be processed into something like::

            ContentsNode([
                LeafASTNode(['\\t', 'key', ' ', 'value']),
                LeafASTNode([' ', '# comment']),
                '\\n'])

        where the ``whitespace`` property for contents would return '\\n'.
        """
        return self._whitespace

    @whitespace.setter
    def whitespace(self, value):
        """Sets trailing whitespace."""
        self._whitespace = value


class LeafASTNode(AbstractASTNode):
    """Creates object containing a simple list of tokens.

    Also manages any preceding whitespace. Can represent a key/value option,
    a comment, or an include/includeoptional directive.

    Examples of what LeafASTNode might look like for different directives::

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

    def __init__(self, raw):
        self._type = raw[0]
        self._raw = tuple(raw[1:])
        self._whitespace = ""
        if len(raw) > 1 and raw[1].isspace():
            self._whitespace = raw[1]
            self._raw = tuple(raw[2:])

    @property
    def typestring(self):
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

            LeafASTNode('\\n  option value').whitespace => "\\n  "
            LeafASTNode('option value').whitespace => ""
            LeafASTNode('\\n  # comment').whitespace => "\\n  "
        """
        return self._whitespace

    @whitespace.setter
    def whitespace(self, value):
        """See base class. Operates on preceding whitespace."""
        self._whitespace = value

    @classmethod
    def parse(cls, raw_str, parser):
        """Factory for :class:`apacheconfig.LeafASTNode` from a config string.

        Args:
            raw_str (string): The text to parse.
            parser (:class:`apacheconfig.ApacheConfigParser`): specify the
                parser to use. Can be created by ``native_apache_parser()``.
        Returns:
            :class:`apacheconfig.LeafASTNode` containing metadata parsed from
            ``raw_str``.
        """
        raw = parser.parse(raw_str)
        return cls(raw[1])

    @property
    def name(self):
        """Returns the name of this node.

        The name is the first non-whitespace token in the directive. Cannot be
        written. For comments, is the entire comment.
        """
        return self._raw[0]

    @property
    def has_value(self):
        """Returns ``True`` if this :class:`apacheconfig.LeafASTNode` has a value.

        ``LeafASTNode`` objects don't have to have a value, like option/value
        directives with no value, or comments.
        """
        return len(self._raw) > 1

    @property
    def value(self):
        """Returns the value of this item as a string.

        The "value" is anything but the name. Can be overwritten.
        """
        if not self.has_value:
            return
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


class BlockNode(LeafASTNode):
    """Creates object containing data for a block.

    Manages any preceding whitespace before the opening block tag, and
    contains a :class:`apacheconfig.ContentsNode` object representing the
    block contents.
    """

    def __init__(self, raw, parser):
        self._whitespace = ""
        self._type = raw[0]
        start = 1
        if isinstance(raw[start], str) and raw[start].isspace():
            self._whitespace = raw[start]
            start += 1
        self._full_tag = LeafASTNode(('statement',) + raw[start])
        self._close_tag = raw[-1]
        self._contents = None
        if len(raw[start + 1]) > 0:
            self._contents = ContentsNode(raw[start + 1], parser)

    @classmethod
    def parse(cls, raw_str, parser):
        """Factory for :class:`apacheconfig.LeafASTNode` from a config string.

        Args:
            raw_str (string): The text to parse.
            parser (:class:`apacheconfig.ApacheConfigParser`): parser object
                to use.
        Returns:
            :class:`apacheconfig.LeafASTNode` containing metadata parsed from
            ``raw_str``.
        """
        raw = parser.parse(raw_str)
        return cls(raw[1], parser)

    @property
    def tag(self):
        """Returns tag name for this block as a string.

        For instance, ``<block details>\\n</block>`` has tag ``"block"``.
        """
        return self._full_tag.name

    @property
    def arguments(self):
        """Returns arguments for this block as a literal string.

        For instance, ``<block lots of details>\\n</block>`` has arguments
         ``"lots of details"``. Can be overwritten.
        """
        return self._full_tag.value

    @arguments.setter
    def arguments(self, arguments):
        """Sets or overwrites arguments for this block."""
        self._full_tag.value = arguments

    @property
    def contents(self):
        """Returns :class:`apacheconfig.ContentsNode` contained within this
        block.
        """
        return self._contents

    @property
    def typestring(self):
        """See base class.

        Can only return ``"block"`` for :class:`apacheconfig.BlockNode`.
        """
        return self._type

    @property
    def whitespace(self):
        """Returns preceding whitespace for this node."""
        return self._whitespace

    @whitespace.setter
    def whitespace(self, value):
        """See base class. Sets preceding whitespace."""
        self._whitespace = value

    def dump(self):
        """See base class."""
        if self._contents is None:
            return "%s<%s/>" % (self.whitespace, self._full_tag.dump())
        return "%s<%s>%s</%s>" % (self.whitespace, self._full_tag.dump(),
                                  self._contents.dump(), self._close_tag)

