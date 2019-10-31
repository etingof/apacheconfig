# http://www.python.org/dev/peps/pep-0396/
__version__ = '0.2.9'

from contextlib import contextmanager

from apacheconfig.lexer import make_lexer
from apacheconfig.parser import make_parser
from apacheconfig.loader import ApacheConfigLoader
from apacheconfig.error import ApacheConfigError

from apacheconfig.wloader import LeafASTNode  # noqa: F401
from apacheconfig.wloader import native_apache_parser  # noqa: F401


@contextmanager
def make_loader(**options):
    ApacheConfigLexer = make_lexer(**options)
    ApacheConfigParser = make_parser(**options)

    yield ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()),
                             **options)


__all__ = ['make_lexer', 'make_parser', 'make_loader',
           'ApacheConfigLoader', 'ApacheConfigError']
