# http://www.python.org/dev/peps/pep-0396/
__version__ = '0.3.3'

from contextlib import contextmanager

from apacheconfig import flavors  # noqa: F401
from apacheconfig.error import ApacheConfigError
from apacheconfig.lexer import make_lexer
from apacheconfig.loader import ApacheConfigLoader
from apacheconfig.parser import make_parser
from apacheconfig.wloader import ApacheConfigWritableLoader


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
