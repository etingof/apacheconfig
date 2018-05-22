# http://www.python.org/dev/peps/pep-0396/
__version__ = '0.1.3'

from contextlib import contextmanager

from apacheconfig.lexer import make_lexer
from apacheconfig.parser import make_parser
from apacheconfig.loader import ApacheConfigLoader
from apacheconfig.error import ApacheConfigError


@contextmanager
def make_loader(**options):
    ApacheConfigLexer = make_lexer(**options)
    ApacheConfigParser = make_parser(**options)

    yield ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()), **options)
