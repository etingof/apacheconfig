
Revision 0.2.8, released 29-12-2018
-----------------------------------

- Copyright notice extended to the year 2019
- Fixed multiline (line continuation) state termination (by an
  empty line)
- Fixed empty continuation line parsing (e.g. just '\')
- Fix to the parser to process empty text on input (and produce
  empty AST)
- Fix to allow quoted and bare paths in the `Include` statement
- The `apacheconfigtool` to respect `--namedblocks` option when
  running in `--json-input` mode

Revision 0.2.7, released 01-09-2018
-----------------------------------

- The `namedblocks` options implemented to allow for disabling tag
  split by the first whitespace and turning it into a nested block.

Revision 0.2.6, released 21-08-2018
-----------------------------------

- Fixed unquoting values when followed by space

Revision 0.2.5, released 15-08-2018
-----------------------------------

- Fixed ply warning on duplicate grammar handler

Revision 0.2.4, released 15-08-2018
-----------------------------------

- Fixed empty named tag parsing

Revision 0.2.3, released 12-08-2018
-----------------------------------

- Added the `nostripvalues` option to right-strip values
  and enabed by default
- Added config file reading abstraction layer to allow for
  non-local config file handling
- Added AST caching to save on repetitive config files includes
- Improved error reporting on parsing errors
- Fixed bug in `mergeduplicateblocks` option implementation
- Fixed HEREDOC parsing to allow indented closing anchor as Perl
  parser seems to do
- Fixed parser grammar inconsistency popping up when `useapacheinclude`
  option is disabled
- Fixed parser grammar to support in-line hash comments

Revision 0.2.2, released 22-07-2018
-----------------------------------

- Added Apache expression tags (ap_expr) test case
- Added support for quoting named blocks
- Added `includeoptional` apacheinclude statement support
- Include and Apache include statements made case-insensitive
- Fixed parser grammar to distinguish <tag /> syntax from <tag/>

Revision 0.2.1, released 18-07-2018
-----------------------------------

- Added explicit ply requirement

Revision 0.2.0, released 14-07-2018
-----------------------------------

- Added `dump()` and `dumps()` methods to render Apache configuration
  back from the `dict`
- The `noescape` option implemented
- Allow empty value syntax in the option-value pair e.g. `option: `
- Fixed a bug causing malformed AST when a comment resides
  in-between duplicate keys

Revision 0.1.4, released 27-05-2018
-----------------------------------

- The `mergeduplicateblocks` option reworked to produce a dict rather than list

Revision 0.1.3, released 22-05-2018
-----------------------------------

- Migrated references to new PyPI
- Fix to tests on Py3.3+

Revision 0.1.2, released 12-04-2018
-----------------------------------

- Adds more options to the apacheconfigtool: --configpath, --flagbits and --defaultconfig

Revision 0.1.1, released 12-04-2018
-----------------------------------

- A bunch of fixes to ensure parsing of the field samples

Revision 0.1.0, released 10-04-2018
-----------------------------------

- Reached feature-parity with Config::General except for the expression support
- Command-line `apacheconfigtool` implemented

Revision 0.0.0, released 18-03-2018
-----------------------------------

- Initial revision

