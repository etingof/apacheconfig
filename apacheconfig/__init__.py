# http://www.python.org/dev/peps/pep-0396/
__version__ = '0.3.1'

from contextlib import contextmanager

from apacheconfig.lexer import make_lexer
from apacheconfig.parser import make_parser
from apacheconfig.loader import ApacheConfigLoader
from apacheconfig.wloader import ApacheConfigWritableLoader
from apacheconfig.error import ApacheConfigError
from apacheconfig import flavors  # noqa: F401


@contextmanager
def make_loader(writable=False, **options):
    ApacheConfigLexer = make_lexer(**options)
    ApacheConfigParser = make_parser(**options)

    if writable:
        options["preservewhitespace"] = True
        yield ApacheConfigWritableLoader(
                ApacheConfigParser(ApacheConfigLexer(), start='contents'),
                **options)
    else:
        yield ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()),
                                 **options)


__all__ = ['make_lexer', 'make_parser', 'make_loader',
           'ApacheConfigLoader', 'ApacheConfigError']
