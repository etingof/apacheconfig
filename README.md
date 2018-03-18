
Apache config parser
--------------------
[![PyPI](https://img.shields.io/pypi/v/apacheconfig.svg?maxAge=2592000)](https://pypi.python.org/pypi/apacheconfig)
[![Python Versions](https://img.shields.io/pypi/pyversions/apacheconfig.svg)](https://pypi.python.org/pypi/apacheconfig/)
[![Build status](https://travis-ci.org/etingof/apacheconfig.svg?branch=master)](https://secure.travis-ci.org/etingof/apacheconfig)
[![Coverage Status](https://img.shields.io/codecov/c/github/etingof/apacheconfig.svg)](https://codecov.io/github/etingof/apacheconfig)
[![GitHub license](https://img.shields.io/badge/license-BSD-blue.svg)](https://raw.githubusercontent.com/etingof/apacheconfig/master/LICENSE.rst)

This is a pure-Python implementation of Apache configuration file parser into Python built-in
types. Similar file format is utilized by Perl's [Config::General](http://search.cpan.org/dist/Config-General/General.pm)
module.

WARNING: this is yet a pretty simplistic parser implementation. In particular, it does not support
expression tags yet.

How to use apacheconfig
-----------------------

With apacheconfig you can build a tree of Python objects from Apache configuration
file.

For example, the following Apache configuration:

```bash
<cops>
  name stein
  age  25
  <colors>
    color \#000000
  </colors>
</cops>
```

Would be transformed by `apacheconfig` into:

```python
{
'cops': {
  'name': 'stein',
  'age': '25',
  'colors': {
    'color': '#000000'
  }
}
```

By running the following code:

```python
from apacheconfig import *

loader = ApacheConfigLoader(ApacheConfigParser(ApacheConfigLexer()))

with open('apache.conf') as f:
    config = loader.loads(f.read())

print(config)
```

How to get apacheconfig
-----------------------

The apacheconfig package is distributed under terms and conditions of 2-clause
BSD [license](https://github.com/etingof/apacheconfig/LICENSE.rst). Source code is freely
available as a GitHub [repo](https://github.com/etingof/apacheconfig).

You could `pip install apacheconfig` or download it from [PyPI](https://pypi.python.org/pypi/apacheconfig).

If something does not work as expected, 
[open an issue](https://github.com/etingof/apacheconfig/issues) at GitHub.

Copyright (c) 2018, [Ilya Etingof](mailto:etingof@gmail.com). All rights reserved.
