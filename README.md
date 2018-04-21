
# Apache-style config parser

[![PyPI](https://img.shields.io/pypi/v/apacheconfig.svg?maxAge=1800)](https://pypi.org/project/apacheconfig)
[![Python Versions](https://img.shields.io/pypi/pyversions/apacheconfig.svg)](https://pypi.org/project/apacheconfig/)
[![Build status](https://travis-ci.org/etingof/apacheconfig.svg?branch=master)](https://secure.travis-ci.org/etingof/apacheconfig)
[![Coverage Status](https://img.shields.io/codecov/c/github/etingof/apacheconfig.svg)](https://codecov.io/github/etingof/apacheconfig)
[![GitHub license](https://img.shields.io/badge/license-BSD-blue.svg)](https://raw.githubusercontent.com/etingof/apacheconfig/master/LICENSE.rst)

This is a pure-Python implementation of Apache-like configuration file parser into Python built-in
types. Similar file format is utilized by Perl's [Config::General](http://search.cpan.org/dist/Config-General/General.pm)
module.

WARNING: this implementation has not fully caught up with the its prototype from the functionality standpoint.
In particular, `apacheconfig` does not support expression tags yet.

## How to use apacheconfig

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

with make_loader() as loader:
    config = loader.load('httpd.conf')

print(config)
```

## Parsing options

Parser behavior can be modified by passing it one or more options. The options are passed as a dictionary:

```python
from apacheconfig import *

options = {
    'lowercasenames': True
}

with make_loader(**options) as loader:
    config = loader.load('httpd.conf')

print(config)
```

The options are largely patterned after Perl's Config::General module, documentation for the options is also
borrowed there.

The following options are currently supported:

### allowmultioptions

If the value is `False`, then multiple identical options are disallowed. The default is `True` in which
case values of the identical options are collected into a list.

### forcearray

You may force a single config line to get parsed into a list by turning on the option *forcearray* and by
surrounding the value of the config entry by *[]*.

Example:

```python
hostlist = [foo.bar]
```

Will result in a single value array entry if the *forcearray* option is turned on.

### lowercasenames

If set to `True`, then all options found in the config will be converted to lowercase. This allows you to
provide case-in-sensitive configs. The values of the options will not lowercased.

### useapacheinclude

If set to `True`, the parser will consider "include ..." as valid include statement (just like the well known
Apache include statement).

### includeagain

If set to `True`, you will be able to include a sub-configfile multiple times. With the default, `False`, duplicate
includes are silently ignored and only the first include will succeed.

Reincluding a configfile can be useful if it contains data that you want to be present in multiple places in the
data tree.

Note, however, that there is currently no check for include recursion.

### includerelative

If set to `True`, included files with a relative path (i.e. "cfg/blah.conf") will be opened from within the location
of the configfile instead from within the location of the script ($0). This works only if the configfile has a
absolute pathname (i.e. "/etc/main.conf").

If the *configpath* option has been set and if the file to be included could not be found in the location relative
to the current config file, the module will search within *configpath* for the file.

### includedirectories

If set to `True`, you may specify include a directory, in which case all files inside the directory will be loaded
in ASCII order. Directory includes will not recurse into subdirectories. This is comparable to including a directory
in Apache-style config files.

### includeglob

If set to `True`, you may specify a glob pattern for an include to include all matching files
(e.g. <<include conf.d/*.conf>>).

An include option will not cause a parser error if the glob didn't return anything.

### configpath

You can use this variable to specify a search path for relative config files which have to be included.
The apacheconfig tool will search within this path for the file if it cannot find the file at the location
relative to the current config file.

To provide multiple search paths you can specify an array reference for the path. For example:

```python

options = {
    'configpath': ['dira', 'dirb']
}
```

### mergeduplicateblocks

If set to `True`, then duplicate blocks, that means blocks and named blocks, will be merged into a single one
The default behavior is to create an array if some junk in a config appears more than once.

### mergeduplicateoptions

If set to `True`, then duplicate options will be merged. That means, if the same option occurs more than once, the
last one will be used in the resulting config dictionary.

### autotrue

If set to `True`, then options in your config file, whose values are set to *true* or *false* values, will be
normalised to *1* or *0* respectively.

The following values will be considered as *true*:

- yes
- on
- 1
- true

The following values will be considered as *false*:

- no
- off
- 0
- false

This effect is case-insensitive, i.e. both *Yes* or *No* will result in *1*.

### flagbits

This option takes one required parameter, which must be a dictionary defining variables for which you want to preset
values. Each variable you have defined in this dictionary and which occurs in your config file, will cause this
variable being set to the preset values to which the value in the config file refers to.

Multiple flags can be used, separated by the pipe character |.

For example, this option:

```python
options = {
    'flagbits': {
        'mode': {
            'CLEAR': '1',
            'STRONG': '1',
            'UNSECURE': '32bit'
        }
    }
}
```

In this example we are defining a variable named *mode* which may contain one or more of *CLEAR*, *STRONG* and
*UNSECURE* as value.

The appropriate config entry may look like this:

```
mode = CLEAR | UNSECURE
```

The parser will create a dictionary which will be the value of the key *mode*. This dictionary will contain all
flags which you have pre-defined, but only those which were set in the config will contain the pre-defined value,
the other ones will be undefined.

The resulting config structure would look like this after parsing:

```python
config = {
    'mode': {
        'CLEAR': '1',
        'UNSECURE': '32bit',
        'STRONG': None
    }
}
```

This method allows the user to set multiple pre-defined values for one option.

Please beware, that all occurrences of those variables will be handled this way, there is no way to distinguish between
variables in different scopes. That means, if *mode* would also occur inside a named block, it would also parsed this
way.

Values which are not defined in the dictionary supplied to the parameter *flagbits* and used in the corresponding
variable in the config will be ignored.

### defaultconfig

The value of this option should be a dictionary holding default options-values. This causes the module to populate
the resulting config dictionary with the given values, which allows you to set default values for particular config
options directly.

Note that you probably want to use this with *mergeduplicateoptions*, otherwise a default value already in the
configuration file will produce an array of two values.

### interpolatevars

If set to `True`, variable interpolation will be done on your config input.

Variables can be defined everywhere in the config and can be used afterwards as the value of an option. Variables
cannot be used as keys or as part of keys.

If you define a variable inside a block or a named block then it is only visible within this block or within blocks
which are defined inside this block.

For example:

```python
# sample config which uses variables
basedir    = /opt/ora
user       = t_space
sys        = unix
<table intern>
 instance  = INTERN
 owner     = $user                 # "t_space"
 logdir    = $basedir/log          # "/opt/ora/log"
 sys       = macos
 <procs>
     misc1 = ${sys}_${instance}    # macos_INTERN
     misc2 = $user                 # "t_space"
 </procs>
</table>
```

This will result in the following structure:

```python
{
  'basedir': '/opt/ora',
  'user': 't_space'
  'sys': 'unix',
  'table': {
    'intern': {
      'sys': 'macos',
      'logdir': '/opt/ora/log',
      'instance': 'INTERN',
      'owner': 't_space',
      'procs': {
        'misc1': 'macos_INTERN',
        'misc2': 't_space'
      }
    }
  }
}
```

As you can see, the variable *sys* has been defined twice. Inside the *<procs>* block a variable *${sys}* has been
used, which then were interpolated into the value of *sys* defined inside the *<table>* block, not the *sys* variable
one level above. If *sys* were not defined inside the *<table>* block then the "global" variable *sys* would have
been used instead with the value of *unix*.

Variables inside double quotes will be interpolated, but variables inside single quotes will not interpolated unless
*allowsinglequoteinterpolation* option is set.

In addition you can surround variable names with curly braces to avoid misinterpretation by the parser.

### interpolateenv

If set to `True`, environment variables can be referenced in configs, their values will be substituted in place of
their reference in the value.

This option enables *interpolatevars*.

### allowsinglequoteinterpolation

By default variables inside single quotes will not be interpolated. If you turn on this option, they will be
interpolated as well.

### strictvars

By default this is set to `True`, which causes parser to fail if an undefined variable with *interpolatevars* turned
on occurs in a config. Set to `False` to avoid such error messages.

### ccomments

The parser will process C-style comments as well as hash-style comments. By default C-style comments are processed,
you can disable that by setting *ccomments* option to `False.

## Parser plugins

You can alter the behavior of the parser by supplying callables which will be invoked on certain hooks during
config file processing and parsing.

The general approach works like this:

```python

def pre_open_hook(file, base):
    print('trying to open %s... ' % file)
    if 'blah' in file:
      print('ignored')
      return False, file, base
    else:
      print('allowed')
      return True, file, base

options = {
    'plug': {
        'pre_open': pre_open_hook
    }
}
```

Output:

```bash
trying to open cfg ... allowed
trying to open x/*.conf ... allowed
trying to open x/1.conf ... allowed
trying to open x/2.conf ... allowed
trying to open x/blah.conf ... ignored
```

As you can see, we wrote a little function which takes a filename and a base directory as parameters. We tell
the parser via the *plug* option to call this sub every time before it attempts to open a file.

General processing continues as usual if the first value of the returned array is `True`. The second value of that
tuple depends on the kind of hook being called.

The following hooks are available so far:

### pre_open

Takes two parameters: *filename* and *basedirectory*.

Has to return a tuple consisting of 3 values:

 - `True` or `False` (continue processing or not)
 - filename
 - base directory

The returned *basedirectory* and *filename* will be used for opening the file.

### pre_read

Takes two parameters: the source of the contents read from and a string containing the raw contents.
This hook gets the unaltered, original contents as it's read from a file (or some other source).

Has to return an array of 3 values:

 - `True` or `False` (continue processing or not)
 - the source of the contents or `None` if `loads()` is invoked rather than `load()`
 - a string that replaces the read contents

You can use this hook to apply your own normalizations or whatever.

## Command-line tool

The library comes with a simple command-line tool `apacheconfigtool` which can convert Apache-style
config files into JSON. The tool is also useful for playing with config file formats and parser
options.

```bash
$ apacheconfigtool  --help
usage: apacheconfigtool [-h] [-v] [--allowmultioptions] [--forcearray]
                        [--lowercasenames] [--useapacheinclude]
                        [--includeagain] [--includerelative]
                        [--includedirectories] [--includeglob]
                        [--mergeduplicateblocks] [--mergeduplicateoptions]
                        [--autotrue] [--interpolatevars] [--interpolateenv]
                        [--allowsinglequoteinterpolation] [--strictvars]
                        [--ccomments]
                        file [file ...]

Dump Apache config files into JSON

positional arguments:
  file                  Path to the configuration file to dump

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit

parsing options:
  --allowmultioptions   Collect multiple identical options into a list
  --forcearray          Force a single config line to get parsed into a list
                        by turning on this option and by surrounding the value
                        of the config entry by []
  --lowercasenames      All options found in the config will be converted to
                        lowercase
  --useapacheinclude    Consider "include ..." as valid include statement
  --includeagain        Allow including sub-configfiles multiple times
  --includerelative     Open included config files from within the location of
                        the configfile instead from within the location of the
                        script
  --includedirectories  Include statement may point to a directory, in which
                        case all files inside the directory will be loaded in
                        ASCII order
  --includeglob         Include statement may point to a glob pattern, in
                        which case all files matching the pattern will be
                        loaded in ASCII order
  --mergeduplicateblocks
                        Duplicate blocks (blocks and named blocks), will be
                        merged into a single one
  --mergeduplicateoptions
                        If the same option occurs more than once, the last one
                        will be used in the resulting config dictionary
  --autotrue            Turn various forms of binary values in config into "1"
                        and "0"
  --interpolatevars     Enable variable interpolation
  --interpolateenv      Enable process environment variable interpolation
  --allowsinglequoteinterpolation
                        Perform variable interpolation even when being in
                        single quotes
  --strictvars          Do not fail on an undefined variable when performing
                        interpolation
  --ccomments           Do not parse C-style comments
  --configpath CONFIGPATH
                        Search path for the configuration files being
                        included. Can repeat.
  --flagbits <JSON>     Named bits for an option in form of a JSON object of
                        the following structure {"OPTION": {"NAME": "VALUE"}}
  --defaultconfig <JSON>
                        Default values for parsed configuration in form of a
                        JSON object

$ apacheconfigtool --includedirectories include-directory-test.conf
{
  "final_include": "true",
  "seen_first_config": "true",
  "seen_second_config": "true",
  "inner": {
    "final_include": "true",
    "seen_third_config": "true"
  },
  "seen_third_config": "true"
}
```

## How to get apacheconfig

The apacheconfig package is distributed under terms and conditions of 2-clause
BSD [license](https://github.com/etingof/apacheconfig/LICENSE.rst). Source code is freely
available as a GitHub [repo](https://github.com/etingof/apacheconfig).

You could `pip install apacheconfig` or download it from [PyPI](https://pypi.org/project/apacheconfig).

If something does not work as expected, 
[open an issue](https://github.com/etingof/apacheconfig/issues) at GitHub.

Copyright (c) 2018, [Ilya Etingof](mailto:etingof@gmail.com). All rights reserved.
