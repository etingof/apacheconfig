# http://www.python.org/dev/peps/pep-0396/
__version__ = '0.2.9'

from contextlib import contextmanager

from apacheconfig.lexer import make_lexer
from apacheconfig.parser import make_parser
from apacheconfig.loader import ApacheConfigLoader
from apacheconfig.error import ApacheConfigError

from apacheconfig.wloader import parse_item, parse_block, parse_contents
from apacheconfig.wloader import ItemNode, BlockNode, ContentsNode


@contextmanager
def make_loader(**options):
    ApacheConfigLexer = make_lexer(**options)
    ApacheConfigParser = make_parser(**options)

    yield ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()),
                             **options)


__all__ = ['parse_item', 'parse_block', 'parse_contents',
           'ItemNode', 'BlockNode', 'ContentsNode',
           'make_lexer', 'make_parser', 'make_loader',
           'ApacheConfigLoader', 'ApacheConfigError']
