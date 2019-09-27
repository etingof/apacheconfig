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
        raise NotImplementedError()

    @property
    def type(self):
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
        """Trailing or preceding whitespace.

        Each Item or BlockNode keeps track of the whitespace preceding it.
        For the first element in the configuration file, there could be no
        whitespace preceding it at all, in which case this should return the
        empty string.

        ContentsNode is special in that it keeps track of the trailing white-
        space.
        """
        if self._whitespace is None:
            raise NotImplementedError()
        return self._whitespace

    @whitespace.setter
    def whitespace(self, value):
        if self._whitespace is None:
            raise NotImplementedError()
        self._whitespace = value


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
        if index + 1 < len(self._contents) and '\n' not in self._contents[index + 1].whitespace:
            self._contents[index + 1].whitespace = '\n' + self._contents[index + 1].whitespace
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
        return "".join([str(item) for item in self._contents]) + self.whitespace


class ItemNode(Node):
    """Contains data for a single configuration line.

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
        return ("ItemNode(%s)"
                % str([self._type] +
                      [_restore_original(word) for word in self._raw]))


class BlockNode(Node):
    """Contains data for a block.

    Manages any preceding whitespace, and details of contents.

    Construct this using raw AST data from parser. Generally, block data looks
    like:
        ['block', <optional whitespace>, <open tag>, <contents object>, <close tag>]
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

def _create_parser(options={}, start='contents'):
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
