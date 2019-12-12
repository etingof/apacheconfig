#
# This file is part of apacheconfig software.
#
# Copyright (c) 2018-2019, Ilya Etingof <etingof@gmail.com>
# License: https://github.com/etingof/apacheconfig/LICENSE.rst
#
from __future__ import unicode_literals

import abc
import six

from apacheconfig.reader import LocalHostReader

from apacheconfig import error


class ApacheConfigWritableLoader(object):
    """Manages a writable object represented by a single config file.

    Args:
        parser (:class:`apacheconfig.ApacheConfigParser`): compiled parser
            to use when loading configuration directives.
        options (dict): keyword args of options to set for loader. Should be
            same set of options passed to parser.
    """

    def __init__(self, parser, **options):
        self._parser = parser
        self._options = dict(options)
        if 'reader' in self._options:
            self._reader = self._options['reader']
        else:
            self._reader = LocalHostReader()

    def load(self, filepath):
        """Loads config file into a raw modifiable AST.

        Args:
            filepath (Text): path of config file to load. Expects UTF-8
                encoding.

        Returns:
            :class:`apacheconfig.ListNode` AST containing parsed config file.

        Raises:
            IOError: If there is a problem opening the file specified.
        """
        with self._reader.open(filepath) as f:
            return self.loads(f.read())

    def loads(self, text):
        """Loads config text into a raw modifiable AST.

        Args:
            text (Text): (Text) containing the configuration to load.

        Returns:
            :class:`apacheconfig.ListNode` AST containing parsed config.
        """
        ast = self._parser.parse(text)
        return ListNode(ast, self._parser)


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

    There are three subclasses: :class:`apacheconfig.ListNode`,
    :class:`apacheconfig.BlockNode`, and :class:`apacheconfig.LeafNode`.

    Every AST should have a :class:`apacheconfig.ListNode` at its root. A
    :class:`apacheconfig.ListNode` or :class:`apacheconfig.BlockNode` can have
    other :class:`apacheconfig.BlockNode`s and
    :class:`apacheconfig.LeafNode`s as children.

    In general, a tree might look like::

                      +----------+
                      | ListNode |
                      +----------+
                       |        |
                       v        v
               +---------+    +--------+
               |BlockNode|    |LeafNode|
               +---------+    +--------+
                |       |
                v       v
        +---------+   +--------+
        |BlockNode|   |LeafNode|
        +---------+   +--------+
           |
           v
          etc...

    Both :class:`apacheconfig.ListNode` and :class:`apacheconfig.BlockNode`
    may contain an ordered list of other nodes, but
    :class:`apacheconfig.LeafNode`s are terminal.

    Each :class:`apacheconfig.AbstractASTNode` class also has their own
    properties and functions. In general, :class:`apacheconfig.LeafNode`
    corresponds with scalar data such as directives/options or comments.
    :class:`apacheconfig.BlockNode` corresponds with an open/close tag and
    its contents.
    """

    @abc.abstractmethod
    def dump(self):
        """Dumps contents of this node.

        Returns:
            (Text) with the contents of this node, as in a config file.
        """

    @abc.abstractproperty
    def typestring(self):
        """Object typestring as defined by the apacheconfig parser.
        """


class ListNode(AbstractASTNode):
    """Creates object for an ordered list of ``apacheconfig.AbstractASTNode``s.

    Every configuration file's root should be a ``apacheconfig.ListNode``.
    Children can be ``apacheconfig.BlockNode`` or ``apacheconfig.LeafNode``.

    Args:
        raw (list): Data returned from ``apacheconfig.parser``. To construct
            from a string containing config directives, use the `parse` factory
            function.

    Raises:
        ApacheConfigError: If `raw` is not formed as expected. In particular,
            if `raw` is too short, or has the wrong `typestring`, or if
            one of this list's children is not formed as expected.
    """
    def __init__(self, raw, parser):
        if len(raw) < 2:
            raise error.ApacheConfigError(
                "Expected properly-formatted `contents` data returned from "
                "``apacheconfig.parser``. Got a list that is too short.")
        self._type = raw[0]
        if self._type != "contents":
            raise error.ApacheConfigError(
                "Expected properly-formatted `contents` data returned from "
                "``apacheconfig.parser``. First element of data is not "
                "\"contents\" typestring.")
        self._contents = []
        self._trailing_whitespace = ""
        self._parser = parser
        for elem in raw[1:]:
            if isinstance(elem, six.string_types) and elem.isspace():
                self._trailing_whitespace = elem
            elif elem[0] == "block":
                self._contents.append(BlockNode(elem, parser))
            elif elem[0] == "contents":
                raise error.ApacheConfigError(
                    "Expected properly-formatted `contents` data returned "
                    "from ``apacheconfig.parser``. Got `contents` data as "
                    "a child of this `contents` data.")
            else:
                self._contents.append(LeafNode(elem))

    @classmethod
    def parse(cls, raw_str, parser):
        """Factory for :class:`apacheconfig.ListNode` from a config string.

        Args:
            raw_str (str): Config string to parse.
            parser (:class:`apacheconfig.ApacheConfigParser`): parser object
                to use.
        Returns:
            :class:`apacheconfig.ListNode` containing data parsed from
            ``raw_str``.
        """
        raw = parser.parse(raw_str)
        return cls(raw, parser)

    def add(self, index, raw_str):
        """Parses and adds child element at given index.

        Parses given string into an :class:`apacheconfig.AbstractASTNode`
        object, then adds to list at specified index.

        Args:
            index (int): index of list at which to insert the node.
            raw_str (str): string to parse. The parser will automatically
                determine whether it's a :class:`apacheconfig.BlockNode` or
                :class:`apacheconfig.LeafNode`.

        Returns:
            The :class:`apacheconfig.AbstractASTNode` created from parsing
                ``raw_str``.

        Raises:
            ApacheConfigError: If `raw_str` cannot be parsed into a
                :class:`apacheconfig.BlockNode` or
                :class:`apacheconfig.LeafNode`.
            IndexError: If `index` is not within bounds [0, len(self)].
        """
        if index < 0 or index > len(self):
            raise IndexError("supplied index is out of range")
        raw = self._parser.parse(raw_str)
        if len(raw) != 2:
            raise error.ApacheConfigError("Given raw_str should be "
                                          "parsable into a single node.")
        raw = self._parser.parse(raw_str)[1]
        if raw[0] == "block":
            node = BlockNode(raw, self._parser)
        else:
            node = LeafNode(raw)

        # If we're adding an element to the beginning of list, the first
        # item may not have a preceding newline-- so we add one in case.
        # For instance, something like:
        #   Contents("line1\nline2").add(0, "\nline0")
        # should end up as "\nline0\nline1\nline2"
        if (index == 0 and self._contents and
           '\n' not in self._contents[0].whitespace):
            whitespace_after = self._contents[0].whitespace
            self._contents[0].whitespace = '\n' + whitespace_after
        self._contents.insert(index, node)
        return node

    def remove(self, index):
        """Removes node from supplied index.

        Args:
            index (int): index of node to remove from list.

        Returns:
            The :class:`apacheconfig.AbstractASTNode` that was removed.

        Raises:
            IndexError: If `index` is not within bounds [0, len(self)).
        """
        if index < 0 or index >= len(self):
            raise IndexError("supplied index is out of range")
        return self._contents.pop(index)

    def __len__(self):
        """Number of :class:`apacheconfig.ASTNode` children."""
        return len(self._contents)

    def __iter__(self):
        """Iterator over :class:`apacheconfig.ASTNode` children."""
        return iter(self._contents)

    def dump(self):
        return ("".join([item.dump() for item in self._contents])
                + self.trailing_whitespace)

    @property
    def typestring(self):
        """See base class.

        Returns:
            ``"contents"`` for :class:`apacheconfig.ListNode`.
        """
        return self._type

    @property
    def trailing_whitespace(self):
        """Trailing whitespace after this list of config items.

        For instance, the following valid configuration::

            \\tkey value # comment\\n

        will be processed into something like::

            ListNode([
                LeafNode(['\\t', 'key', ' ', 'value']),
                LeafNode([' ', '# comment']),
                '\\n'])

        where the ``trailing_whitespace`` property would return '\\n'.

        Returns:
            String containing trailing whitespace after this list in the
            config file.
        """
        return self._trailing_whitespace

    @trailing_whitespace.setter
    def trailing_whitespace(self, value):
        """Sets trailing whitespace after this list of config items.

        Args:
            value (Text): Trailing whitespace for this list of config items.
        """
        self._trailing_whitespace = value


class LeafNode(AbstractASTNode):
    """Creates object containing a simple list of tokens.

    Also manages any preceding whitespace. Can represent a key/value option,
    a comment, or an include/includeoptional directive.

    Examples of what LeafNode might look like for different directives::

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

    Raises:
        ApacheConfigError: If `raw` is not formed as expected. In particular,
            if `raw` is too short or has the wrong `typestring`.
    """

    def __init__(self, raw):
        if len(raw) < 2:
            raise error.ApacheConfigError(
                "Expected properly-formatted data returned from "
                "``apacheconfig.parser``. Got a list that is too short.")
        self._type = raw[0]
        if self._type == "contents" or self._type == "block":
            raise error.ApacheConfigError(
                "Expected properly-formatted data returned from "
                "``apacheconfig.parser``. First element of data cannot "
                "be \"contents\" or \"block\" typestring.")
        self._raw = tuple(raw[1:])
        self._whitespace = ""
        if len(raw) > 1 and raw[1].isspace():
            self._whitespace = raw[1]
            self._raw = tuple(raw[2:])

    @property
    def typestring(self):
        """See base class.

        Returns:
            The typestring (as defined by the apacheconfig parser) for
            this node. The possible values for this are ``"comment"``,
            ``"statement"``, ``"include"``, ``"includeoptional"``.
        """
        return self._type

    @property
    def whitespace(self):
        """Whitespace preceding this element in the config file.

        For example::

            LeafNode('\\n  option value').whitespace => "\\n  "
            LeafNode('option value').whitespace => ""
            LeafNode('\\n  # comment').whitespace => "\\n  "

        Returns:
            String containing preceding whitespace for this node.
        """
        return self._whitespace

    @whitespace.setter
    def whitespace(self, value):
        """Sets whitespace preceding this element in the config file.

        Args:
            value (str): New whitespace to set.
        """
        self._whitespace = value

    @classmethod
    def parse(cls, raw_str, parser):
        """Factory for :class:`apacheconfig.LeafNode` from a config string.

        Args:
            raw_str (Text): The text to parse, as a unicode string.
            parser (:class:`apacheconfig.ApacheConfigParser`): specify the
                parser to use. Can be created by ``native_apache_parser()``.
        Returns:
            :class:`apacheconfig.LeafNode` containing metadata parsed from
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
        """Returns ``True`` if this :class:`apacheconfig.LeafNode` has a value.

        ``LeafNode`` objects don't have to have a value, like option/value
        directives with no value, or comments.
        """
        return len(self._raw) > 1

    @property
    def value(self):
        """Returns the value of this item as a unicode string.

        The "value" is anything but the name. Can be overwritten.
        """
        if not self.has_value:
            return
        return self._raw[-1]

    @value.setter
    def value(self, value):
        """Sets for the value of this item.

        Args:
            value (Text): string to set new value to.

          .. todo:: (sydneyli) convert `value` to quotedstring when quoted
        """
        if not self.has_value:
            self._raw = self._raw + (" ", value,)
        self._raw = self._raw[0:-1] + (value,)

    def dump(self):
        return (self.whitespace +
                "".join([_restore_original(word) for word in self._raw]))

    def __str__(self):
        contents = [_restore_original(word) for word in self._raw]
        return ("%s(%s)"
                % (str(self.__class__.__name__),
                   str([self._type] + contents)))

    def __unicode__(self):
        contents = [_restore_original(word) for word in self._raw]
        return ("%s(%s)"
                % (six.text_type(self.__class__.__name__),
                   six.text_type([self._type] + contents)))


class BlockNode(ListNode):
    """Creates object containing data for a block.

    Manages any preceding whitespace before the opening block tag, and
    superclass :class:`apacheconfig.ListNode` methods will manipulate
    block contents.

    Args:
        raw (list): Data returned from ``apacheconfig.parser``. To construct
            from a string containing a config block, use the `parse` factory
            function.

    Raises:
        ApacheConfigError: If `raw` is not formed as expected. In particular,
            if `raw` is too short, or has the wrong `typestring`, or if
            data for this block or one of this block's children is not formed
            as expected.
    """

    def __init__(self, raw, parser):
        if len(raw) < 4:
            raise error.ApacheConfigError(
                "Expected properly-formatted data returned from "
                "``apacheconfig.parser``. Got a list that is too short.")
        self._whitespace = ""
        self._type = raw[0]
        if self._type != "block":
            raise error.ApacheConfigError(
                "Expected properly-formatted data returned from "
                "``apacheconfig.parser``. First element of data is not "
                "\"block\" typestring.")
        start = 1
        if isinstance(raw[start], six.string_types) and raw[start].isspace():
            self._whitespace = raw[start]
            start += 1
        self._full_tag = LeafNode(('statement',) + raw[start])
        self._close_tag = raw[-1]
        self._contents = None
        if raw[start + 1]:  # If we have a list of elements to process.
            super(BlockNode, self).__init__(raw[start + 1], parser)
        self._type = raw[0]

    @classmethod
    def parse(cls, raw_str, parser):
        """Factory for :class:`apacheconfig.BlockNode` from a config string.

        Args:
            raw_str (str): The text to parse.
            parser (:class:`apacheconfig.ApacheConfigParser`): parser object
                to use.
        Returns:
            :class:`apacheconfig.BlockNode` containing metadata parsed from
            ``raw_str``.
        """
        raw = parser.parse(raw_str)
        return cls(raw[1], parser)

    @property
    def tag(self):
        """Tag name for this block.

        Returns:
            Tag name for this blog as a string. For instance,
            ``<block details>\\n</block>`` has tag ``"block"``.
        """
        return self._full_tag.name

    @property
    def arguments(self):
        """Arguments of this block.

        Returns:
            Arguments for this block as a string. For instance,
            ``<block lots of \tdetails>\\n</block>`` returns arguments
            ``"lots of \tdetails"``. Can be overwritten.
        """
        return self._full_tag.value

    @arguments.setter
    def arguments(self, arguments):
        """Sets or overwrites arguments for this block.

        Args:
            arguments (str): New arguments for this block.
        """
        self._full_tag.value = arguments

    @property
    def typestring(self):
        """See base class.

        Returns:
            ``"block"`` for :class:`apacheconfig.BlockNode`.
        """
        return self._type

    @property
    def whitespace(self):
        """Whitespace preceding this element in the config file.

        Returns:
            String containing preceding whitespace for this node.
        """
        return self._whitespace

    @whitespace.setter
    def whitespace(self, value):
        """Sets whitespace preceding this element in the config file.

        Args:
            value (str): New whitespace to set.
        """
        self._whitespace = value

    def dump(self):
        if self._contents is None:
            return "%s<%s/>" % (self.whitespace, self._full_tag.dump())
        contents = super(BlockNode, self).dump()
        return "%s<%s>%s</%s>" % (self.whitespace, self._full_tag.dump(),
                                  contents, self._close_tag)
