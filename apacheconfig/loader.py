#
# This file is part of apacheconfig software.
#
# Copyright (c) 2018, Ilya Etingof <etingof@gmail.com>
# License: https://github.com/etingof/apacheconfig/LICENSE.rst
#
import logging

from apacheconfig.error import ApacheConfigError

log = logging.getLogger(__name__)


class ApacheConfigLoader(object):

    def __init__(self, parser, debug=False):
        self._parser = parser
        self._debug = debug

    # Code generation rules

    def g_config(self, ast):
        config = {}

        for subtree in ast:
            items = self._walkast(subtree)
            if items:
                config.update(items)

        return config

    def g_block(self, ast):
        block = {
            ast[0]: {}
        }

        for subtree in ast[1:-1]:
            items = self._walkast(subtree)
            if items:
                block[ast[0]].update(items)

        return block

    def g_contents(self, ast):
        contents = {}

        for subtree in ast:
            items = self._walkast(subtree)
            if items:
                contents.update(items)

        return contents

    def g_statements(self, ast):
        statements = {}

        for subtree in ast:
            items = self._walkast(subtree)
            for item in items:
                if item in statements:
                    if not isinstance(statements[item], list):
                        statements[item] = [statements[item]]
                    statements[item].append(items[item])
                else:
                    statements[item] = items[item]

        return statements

    def g_statement(self, ast):
        return {
            ast[0]: ast[1]
        }


    def g_comment(self, ast):
        return []

    def _walkast(self, ast):
        if not ast:
            return

        node_type = ast[0]

        try:
            handler = getattr(self, 'g_' + node_type)

        except AttributeError:
            raise ApacheConfigError('Unsupported AST node type %s' % node_type)

        return handler(ast[1:])

    def loads(self, text):
        ast = self._parser.parse(text)

        return self._walkast(ast)
