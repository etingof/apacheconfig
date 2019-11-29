#
# This file is part of apacheconfig software.
#
# Copyright (c) 2018-2019, Ilya Etingof <etingof@gmail.com>
# License: https://github.com/etingof/apacheconfig/LICENSE.rst
#
from __future__ import unicode_literals

import glob
import io
import logging
import re
import os
import tempfile
import six

from apacheconfig import error
from apacheconfig.reader import LocalHostReader

log = logging.getLogger(__name__)


class ApacheConfigLoader(object):

    def __init__(self, parser, debug=False, **options):
        self._parser = parser
        self._debug = debug
        self._options = dict(options)
        if 'reader' in self._options:
            self._reader = self._options['reader']
        else:
            self._reader = LocalHostReader()
        self._stack = []
        self._includes = set()
        self._ast_cache = {}

    # Code generation rules

    def g_config(self, ast):
        config = {}

        for subtree in ast:
            items = self._walkast(subtree)
            if items:
                config.update(items)

        return config

    @staticmethod
    def _unquote_tag(tag):
        if tag[0] == '"' and tag[-1] == '"':
            tag = tag[1:-1]
        if tag[0] == "'" and tag[-1] == "'":
            tag = tag[1:-1]

        if not tag:
            raise error.ApacheConfigError('Empty block tag not allowed')

        return tag

    def g_block(self, ast):
        tag = ast[0]
        values = {}

        if not self._options.get('namedblocks', True):
            tag = ("".join(tag),)
        if len(tag) > 1:
            name, _, value = tag
            block = {
                name: {
                    value: values
                }
            }
        else:
            tag = self._unquote_tag(tag[0])

            block = {
                tag: values
            }

        for subtree in ast[1:-1]:
            items = self._walkast(subtree)
            if items:
                values.update(items)

        return block

    def g_contents(self, ast):
        # TODO(etingof): remove defaulted and overridden options from
        # productions
        contents = self._options.get('defaultconfig', {})

        for subtree in ast:
            items = self._walkast(subtree)
            self._merge_contents(contents, items)

        return contents

    def _interpolate_vars(self, option, value):
        """Store option / values in `stack` and interpolate value when referenced.
        Returns `value` with any interpolated variables.
        """
        if (self._options.get('interpolateenv', False) or
                self._options.get('allowsinglequoteinterpolation', False)):
            self._options['interpolatevars'] = True

        if self._options.get('interpolatevars', False):
            def lookup(match):
                option = match.groups()[0]

                for frame in self._stack:
                    if option in frame:
                        return interpolate(frame[option])

                if self._options.get('interpolateenv', False):
                    if option in self._reader.environ:
                        return interpolate(self._reader.environ[option])

                if self._options.get('strictvars', True):
                    raise error.ApacheConfigError(
                        'Undefined variable "${%s}" referenced' % option)

                return interpolate(match.string)

            def interpolate(value):
                expanded = re.sub(r'(?<!\\)\${([^\n\r]+?)}', lookup, value)
                if expanded != value:
                    return expanded
                return re.sub(r'(?<!\\)\$([^\n\r $]+?)', lookup, value)

            if (not getattr(value, 'is_single_quoted', False) or
                    self._options.get('allowsinglequoteinterpolation', False)):
                if isinstance(value, list):
                    value = [interpolate(x) for x in value]
                else:
                    value = interpolate(value)

        self._stack.insert(0, {option: value})
        return value

    def g_statement(self, ast):
        """Performs postprocessing on a statement. Returns an {option: value} dict.
        """
        if len(ast) == 1:
            return {ast[0]: None}
        option, value = ast[:2]
        value = self._interpolate_vars(option, value)

        def remove_escapes(value):
            if self._options.get('noescape'):
                return value
            if not isinstance(value, six.text_type):
                return value
            return re.sub(r'\\([$\\"#])', lambda x: x.groups()[0], value)
        if isinstance(value, list):
            value = [remove_escapes(x) for x in value]
        else:
            value = remove_escapes(value)

        flagbits = self._options.get('flagbits')
        if flagbits and option in flagbits:
            flags = dict([(key, None) for key in flagbits[option]])
            for flag in value.split('|'):
                flag = flag.strip()
                flags[flag] = flagbits[option][flag]
            value = flags

        elif self._options.get('autotrue'):
            if value.lower() in ('yes', 'on', 'true'):
                value = '1'
            elif value.lower() in ('no', 'off', 'false'):
                value = '0'

        if self._options.get('forcearray'):
            if value.startswith('[') and value.endswith(']'):
                value = [value[1:-1]]

        return {
            option: value
        }

    def g_comment(self, ast):
        return []

    def g_includeoptional(self, ast):
        try:
            return self.g_include(ast)

        except error.ConfigFileReadError:
            return {}

    def g_include(self, ast):
        filepath = self._unquote_tag(ast[0])

        options = self._options

        if os.path.isabs(filepath):
            configpath = [os.path.dirname(filepath)]
            filename = os.path.basename(filepath)

        else:
            configpath = options.get('configpath', [])

            if 'configroot' in options and options.get('includerelative'):
                configpath.insert(0, options['configroot'])

            if 'programpath' in options:
                configpath.append(options['programpath'])
            else:
                configpath.append('.')

            if self._reader.isdir(filepath):
                configpath.insert(0, filepath)
                filename = '.'
            else:
                filename = filepath

        for configdir in configpath:

            filepath = os.path.join(configdir, filename)

            if self._reader.isdir(filepath):
                if options.get('includedirectories'):
                    contents = {}

                    for include_file in sorted(self._reader.listdir(filepath)):
                        items = self.load(os.path.join(
                            filepath, include_file), initialize=False)
                        self._merge_contents(contents, items)

                    return contents

            elif options.get('includeglob'):
                contents = {}

                for include_file in sorted(glob.glob(filepath)):
                    items = self.load(include_file, initialize=False)
                    self._merge_contents(contents, items)

                return contents

            elif self._reader.exists(filepath):
                return self.load(filepath, initialize=False)

        else:
            raise error.ConfigFileReadError(
                'Config file "%s" not found in search path %s'
                % (filename, ':'.join(configpath)))

    def _merge_contents(self, contents, items):
        """Merges items into existing contents dictionary.
        Returns new contents.
        """
        for item in items:
            contents = self._merge_item(contents, item, items[item])
        return contents

    def _merge_item(self, contents, key, value, path=[]):
        """Merges a single "key, value" item into contents dictionary, and
        returns new contents. Merging rules differ depending on flags set,
        and whether `value` is a dictionary (block).
        """
        if key not in contents:
            contents[key] = value
            return contents

        # In case of duplicate keys, AST can contain a list of values.
        # Here all values forced into being a list to unify further processing.
        if isinstance(value, list):
            vector = value
        else:
            vector = [value]

        if isinstance(value, dict):  # Merge block into contents
            if self._options.get('mergeduplicateblocks'):
                contents = self._merge_dicts(contents[key], value)
            else:
                if not isinstance(contents[key], list):
                    contents[key] = [contents[key]]
                contents[key] += vector
        else:  # Merge statement/option into contents
            if not self._options.get('allowmultioptions', True) \
                    and not self._options.get('mergeduplicateoptions', False):
                raise error.ApacheConfigError(
                    'Duplicate option "%s" prohibited'
                    % '.'.join(path + [six.text_type(key)]))
            if self._options.get('mergeduplicateoptions', False):
                contents[key] = value
            else:
                if not isinstance(contents[key], list):
                    contents[key] = [contents[key]]
                contents[key] += vector
        return contents

    def _merge_dicts(self, dict1, dict2, path=[]):
        """Merges items from dict2 into dict1."""
        for key in dict2:
            dict1 = self._merge_item(dict1, key, dict2[key], path)
        return dict1

    def _merge_lists(self, list1, list2):
        for item in list2:
            if item not in list1:
                list1.append(item)
        return list1

    def _walkast(self, ast):
        if not ast:
            return

        node_type = ast[0]

        try:
            handler = getattr(self, 'g_' + node_type)

        except AttributeError:
            raise error.ApacheConfigError(
                'Unsupported AST node type %s' % node_type)

        return handler(ast[1:])

    def loads(self, text, initialize=True, source=None):
        """Loads config text into a dictionary object.

        Args:
            text (Text): (Text) containing the configuration to load.

        Returns:
            (dict) containing configuration information loaded from text.
        """
        if not text:
            self._ast_cache[source] = {}
            return {}

        if initialize:
            self._stack = []

        try:
            pre_read = self._options['plug']['pre_read']

            process, source, text = pre_read(source, text)

            if not process:
                self._ast_cache[source] = {}
                return {}

        except KeyError:
            pass

        ast = self._parser.parse(text)

        self._ast_cache[source] = self._walkast(ast)
        return self._ast_cache[source]

    def load(self, filepath, initialize=True):
        """Loads config file into a dictionary object.

        Args:
            filepath (Text): path of config file to load. Expects UTF-8
                encoding.

        Returns:
            dict containing configuration information loaded from file.
        """
        if initialize:
            self._stack = []
            self._includes = set()
            self._ast_cache = {}

        try:
            pre_open = self._options['plug']['pre_open']

            filename, basedir = os.path.basename(
                filepath), os.path.dirname(filepath)

            process, filename, basedir = pre_open(filename, basedir)

            filepath = os.path.join(
                basedir, filename) if basedir else filename

            if not process:
                return {}

        except KeyError:
            pass

        if filepath in self._includes and not self._options.get(
                'includeagain'):
            return {}

        self._includes.add(filepath)

        if filepath in self._ast_cache:
            return self._ast_cache[filepath]

        try:
            with self._reader.open(filepath) as f:
                return self.loads(f.read(), source=filepath)

        except IOError as ex:
            raise error.ConfigFileReadError('File %s can\'t be open: %s'
                                            % (filepath, ex))

        finally:
            if initialize:
                self._ast_cache = {}

    def _dumpdict(self, obj, indent=0, continue_tag=False):
        if not isinstance(obj, dict):
            raise error.ApacheConfigError('Unknown object type "%r" to dump'
                                          % obj)

        text = ''
        spacing = ' ' * indent

        for key, val in obj.items():
            if isinstance(val, six.text_type):
                if val.isalnum():
                    text += '%s%s %s\n' % (spacing, key, val)
                else:
                    text += '%s%s "%s"\n' % (spacing, key, val)

            elif isinstance(val, list):
                for dup in val:
                    if isinstance(dup, six.text_type):
                        if dup.isalnum():
                            text += '%s%s %s\n' % (spacing, key, dup)
                        else:
                            text += '%s%s "%s"\n' % (spacing, key, dup)
                    else:
                        if self._options.get('namedblocks', True):
                            text += ('%s<%s>\n%s%s</%s>\n'
                                     % (spacing, key,
                                        self._dumpdict(dup, indent + 2),
                                        spacing, key))
                        else:
                            text += ('%s<%s %s%s</%s>\n'
                                     % (spacing, key,
                                        self._dumpdict(dup, indent + 2,
                                                       continue_tag=True),
                                        spacing, key))

            else:
                if self._options.get('namedblocks', True):
                    text += ('%s<%s>\n%s%s</%s>\n'
                             % (spacing, key, self._dumpdict(val, indent + 2),
                                spacing, key))
                else:
                    if continue_tag:
                        text += ('%s>\n%s'
                                 % (key, self._dumpdict(val, indent + 2)))
                    else:
                        text += ('%s<%s %s%s</%s>\n'
                                 % (spacing, key,
                                    self._dumpdict(val, indent + 2,
                                                   continue_tag=True),
                                    spacing, key))
        return text

    def dumps(self, dct):
        """Dumps the configuration in `dct` to a unicode string.

        Args:
            dct (dict): Configuration represented as a dictionary.

        Returns:
            (Text) containing the configuration in given dictionary.
        """
        return self._dumpdict(dct)

    def dump(self, filepath, dct):
        """Dumps the configuration in `dct` to a file.

        Args:
            filepath (Text): Filepath to write config to, in UTF-8 encoding.
            dct (dict): Configuration represented as a dictionary.
        """
        tmpf = tempfile.NamedTemporaryFile(dir=os.path.dirname(filepath),
                                           delete=False)

        try:
            with io.open(tmpf.name, mode='w', encoding='utf-8') as f:
                f.write(self.dumps(dct))

            os.rename(tmpf.name, filepath)

        except IOError as ex:
            try:
                os.unlink(tmpf.name)

            except Exception:
                pass

            raise error.ApacheConfigError('File %s can\'t be written: %s'
                                          % (filepath, ex))
