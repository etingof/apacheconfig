#
# This file is part of apacheconfig software.
#
# Copyright (c) 2018, Ilya Etingof <etingof@gmail.com>
# License: https://github.com/etingof/apacheconfig/LICENSE.rst
#
import glob
import logging
import re
import os
import tempfile

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

        if (self._options.get('namedblocks', True) and
                re.match(r'[^"\'].*?[ \t\r\n]+.*?[^"\']', tag)):
            tag, name = re.split(r'[ \t\r\n]+', tag, maxsplit=1)

            name = self._unquote_tag(name)

            block = {
                tag: {
                    name: values
                }
            }

        else:
            tag = self._unquote_tag(tag)

            block = {
                tag: values
            }

        for subtree in ast[1:-1]:
            items = self._walkast(subtree)
            if items:
                values.update(items)

        return block

    def g_contents(self, ast):
        # TODO(etingof): remove defaulted and overridden options from productions
        contents = self._options.get('defaultconfig', {})

        for subtree in ast:
            items = self._walkast(subtree)
            self._merge_contents(contents, items)

        return contents

    def g_statements(self, ast):
        statements = {}

        for subtree in ast:
            items = self._walkast(subtree)
            for item in items:
                if item in statements:
                    if (self._options.get('allowmultioptions', True) and
                            not self._options.get('mergeduplicateoptions', False)):
                        if not isinstance(statements[item], list):
                            statements[item] = [statements[item]]
                        statements[item].append(items[item])
                    elif self._options.get('mergeduplicateoptions', False):
                        statements[item] = items[item]
                    else:
                        raise error.ApacheConfigError('Duplicate option "%s" prohibited' % item)
                else:
                    statements[item] = items[item]

        if (self._options.get('interpolateenv', False) or
                self._options.get('allowsinglequoteinterpolation', False)):
            self._options['interpolatevars'] = True

        if self._options.get('interpolatevars', False):

            def lookup(match):
                option = match.groups()[0]

                if option in statements:
                    return interpolate(statements[option])

                for frame in self._stack:
                    if option in frame:
                        return interpolate(frame[option])

                if self._options.get('interpolateenv', False):
                    if option in self._reader.environ:
                        return interpolate(self._reader.environ[option])

                if self._options.get('strictvars', True):
                    raise error.ApacheConfigError('Undefined variable "${%s}" referenced' % option)

                return interpolate(match.string)

            def interpolate(value):
                expanded = re.sub(r'(?<!\\)\${([^\n\r]+?)}', lookup, value)
                if expanded != value:
                    return expanded
                return re.sub(r'(?<!\\)\$([^\n\r $]+?)', lookup, value)

            for option, value in tuple(statements.items()):
                if (not getattr(value, 'is_single_quoted', False) or
                        self._options.get('allowsinglequoteinterpolation', False)):
                    if isinstance(value, list):
                        statements[option] = [interpolate(x) for x in value]
                    else:
                        statements[option] = interpolate(value)

        def remove_escapes(value):
            if self._options.get('noescape'):
                return value
            if not isinstance(value, str):
                return value
            return re.sub(r'\\([$\\"#])', lambda x: x.groups()[0], value)

        for option, value in tuple(statements.items()):
            if isinstance(value, list):
                statements[option] = [remove_escapes(x) for x in value]
            else:
                statements[option] = remove_escapes(value)

        self._stack.insert(0, statements)

        return statements

    def g_statement(self, ast):
        option, value = ast[:2]

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
        filepath = ast[0]

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
            raise error.ConfigFileReadError('Config file "%s" not found in search path %s' % (filename, ':'.join(configpath)))

    def _merge_contents(self, contents, items):
        for item in items:
            # In case of duplicate keys, AST can contain a list of values.
            # Here all values forced into being a list to unify further processing.
            if isinstance(items[item], list):
                vector = items[item]
            else:
                vector = [items[item]]

            if item in contents:
                # TODO(etingof): keep block/statements merging at one place
                if self._options.get('mergeduplicateblocks'):
                    contents = self._merge_dicts(contents, items)
                else:
                    if not isinstance(contents[item], list):
                        contents[item] = [contents[item]]
                    contents[item].extend(vector)
            else:
                contents[item] = items[item]

        return contents

    def _merge_dicts(self, dict1, dict2, path=[]):
        "merges dict2 into dict1"
        for key in dict2:
            if key in dict1:
                if isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
                    self._merge_dicts(dict1[key], dict2[key], path + [str(key)])
                elif dict1[key] != dict2[key]:
                    if self._options.get('allowmultioptions', True):
                        if not isinstance(dict1[key], list):
                            dict1[key] = [dict1[key]]
                        if not isinstance(dict2[key], list):
                            dict2[key] = [dict2[key]]
                        dict1[key] = self._merge_lists(dict1[key], dict2[key])
                    else:
                        if self._options.get('mergeduplicateoptions', False):
                            dict1[key] = dict2[key]
                        else:
                            raise error.ApacheConfigError('Duplicate option "%s" prohibited' % '.'.join(path + [str(key)]))
            else:
                dict1[key] = dict2[key]
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
            raise error.ApacheConfigError('Unsupported AST node type %s' % node_type)

        return handler(ast[1:])

    def loads(self, text, initialize=True, source=None):
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

        if filepath in self._includes and not self._options.get('includeagain'):
            return {}

        self._includes.add(filepath)

        if filepath in self._ast_cache:
            return self._ast_cache[filepath]

        try:
            with self._reader.open(filepath) as f:
                return self.loads(f.read(), source=filepath)

        except IOError as ex:
            raise error.ConfigFileReadError('File %s can\'t be open: %s' % (filepath, ex))

        finally:
            if initialize:
                self._ast_cache = {}

    def _dumpdict(self, obj, indent=0):
        if not isinstance(obj, dict):
            raise error.ApacheConfigError('Unknown object type "%r" to dump' % obj)

        text = ''
        spacing = ' ' * indent

        for key, val in obj.items():
            if isinstance(val, str):
                if val.isalnum():
                    text += '%s%s %s\n' % (spacing, key, val)
                else:
                    text += '%s%s "%s"\n' % (spacing, key, val)

            elif isinstance(val, list):
                for dup in val:
                    if isinstance(dup, str):
                        if dup.isalnum():
                            text += '%s%s %s\n' % (spacing, key, dup)
                        else:
                            text += '%s%s "%s"\n' % (spacing, key, dup)
                    else:
                        text += '%s<%s>\n%s%s</%s>\n' % (spacing, key, self._dumpdict(dup, indent + 2), spacing, key)

            else:
                text += '%s<%s>\n%s%s</%s>\n' % (spacing, key, self._dumpdict(val, indent + 2), spacing, key)

        return text

    def dumps(self, dct):
        return self._dumpdict(dct)

    def dump(self, filepath, dct):
        tmpf = tempfile.NamedTemporaryFile(dir=os.path.dirname(filepath), delete=False)

        try:
            with open(tmpf.name, 'w') as f:
                f.write(self.dumps(dct))

            os.rename(tmpf.name, filepath)

        except IOError as ex:
            try:
                os.unlink(tmpf.name)

            except Exception:
                pass

            raise error.ApacheConfigError('File %s can\'t be written: %s' % (filepath, ex))
