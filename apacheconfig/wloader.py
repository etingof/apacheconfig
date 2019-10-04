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


class ContentsNode(Node):
    """Node representing an ordered list of BlockNodes and ItemNodes.

    Each BlockNode contains a ContentsNode, and every configuration's root is
    a ContentsNode.

    Unlike other Nodes, the `whitespace` property of ContentsNode keeps track
    of *trailing* whitespace, since the preceding whitespace in ContentsNode
    will already be recorded by the first Item or Block in ContentsNode.

    For instance, the following valid configuration:
        `\tkey value # comment\n`
    will be processed into something like:
        ContentsNode([
            ItemNode(['\t', 'key', ' ', 'value']),
            ItemNode([' ', '# comment']),
            '\n'])
    where the `whitespace` property for contents would return '\n', not '\t'.
    """
    def __init__(self, raw):
        self._type = raw[0]
        self._contents = []
        self._whitespace = ""
        for elem in raw[1:]:
            if isinstance(elem, str) and elem.isspace():
                self._whitespace = elem
            elif elem[0] == "block":
                self._contents.append(BlockNode(elem))
            else:
                self._contents.append(ItemNode(elem))

    def add(self, index, raw_str):
        """Parses thing into an Item or Block Node, then adds to contents.

        Arguments:
            raw_str: string to parse. The parser should be able to determine
                     whether it's a block or item. For instance:
                       `key value`
                       `<empty block/>`
            whitespace: preceding whitespace to prepend to the item.
            index:   index of contents at which to insert the resulting node.
        """
        parser = _create_parser({}, start='miditem')
        raw = parser.parse(raw_str)
        if raw[0] == "block":
            node = BlockNode(raw)
        else:
            node = ItemNode(raw)
        self._contents.insert(index, node)
        if (index + 1 < len(self._contents) and
           '\n' not in self._contents[index + 1].whitespace):
            whitespace_after = self._contents[index + 1].whitespace
            self._contents[index + 1].whitespace = '\n' + whitespace_after
        return node

    def remove(self, index):
        """Removes node/thing from supplied index.

        Arguments:
            index: index of node to remove from contents.
        """
        thing = self._contents[index]
        del self._contents[index]
        return thing

    def __len__(self):
        return len(self._contents)

    def __iter__(self):
        return iter(self._contents)

    def __str__(self):
        return ("".join([str(item) for item in self._contents])
                + self.whitespace)


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


class BlockNode(Node):
    """Contains data for a block.

    Manages any preceding whitespace, and details of contents.

    Construct this using raw AST data from parser. Generally, block data looks
    like:
        ['block', <optional whitespace>, <open tag>, <contents object>,
            <close tag>]
    E.g., for the block "<block_tag block_args>

    <block/> is represented with an empty contents object.

    The add/remove functions inherited from ContentsNode act on the contents
    contained within this block.

    Properties:
        tag:  getter only. Retrieves the full tag name.
        arguments:  getter & setter for block arguments.
    """

    def __init__(self, raw):
        self._whitespace = ""
        self._type = raw[0]
        start = 1
        if isinstance(raw[start], str) and raw[start].isspace():
            self._whitespace = raw[start]
            start += 1
        self._full_tag = ItemNode(('statement',) + raw[start])
        self._close_tag = raw[-1]
        self._contents = None
        if len(raw[start+1]) > 0:
            self._contents = ContentsNode(raw[start + 1])

    @property
    def tag(self):
        return self._full_tag.name

    @property
    def arguments(self):
        return self._full_tag.value

    @arguments.setter
    def arguments(self, arguments):
        self._full_tag.value = arguments

    @property
    def contents(self):
        return self._contents

    def __str__(self):
        if self._contents is None:
            return "%s<%s/>" % (self.whitespace, str(self._full_tag))
        return "%s<%s>%s</%s>" % (self.whitespace, str(self._full_tag),
                                  str(self._contents), self._close_tag)


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


def parse_contents(raw_str, options={}):
    parser = _create_parser(options, start='contents')
    return ContentsNode(parser.parse(raw_str))


def parse_item(raw_str, options={}):
    parser = _create_parser(options, start='startitem')
    return ItemNode(parser.parse(raw_str))


def parse_block(raw_str, options={}):
    parser = _create_parser(options, start='startitem')
    return BlockNode(parser.parse(raw_str))
