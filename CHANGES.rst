
Revision 0.2.2, released 22-07-2018
-----------------------------------

- Added Apache expression tags (ap_expr) test case
- Added support for quoting named blocks
- Added `includeoptinal` apacheinclude statement support
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

