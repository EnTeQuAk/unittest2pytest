# -*- coding: utf-8 -*-
from lib2to3.fixer_base import BaseFix
from lib2to3.fixer_util import (
    Comma, Name, Call, Node, Leaf,
    Newline, KeywordArg, find_indentation,
    ArgList, String, Number, syms, token)

from functools import partial
import re
import unittest


def strip_newlines(node):
    # This is probably stupid but there are tools that are capable
    # of fixing this a lot better than we ever could do here so we're just
    # stripping weird and customized indentation and be happy about it.
    if isinstance(node, Node) and node.children:
        for child in node.children:
            if isinstance(child, Node):
                strip_newlines(child)

            if '\n' in child.prefix:
                child.prefix = ' '


class FixNose(BaseFix):
    PATTERN = """
    power< func='eq_'
        trailer< '(' arglist=any ')' >
    >
    """

    def transform(self, node, results):
        def process_arg(arg):
            if isinstance(arg, Leaf) and arg.type == token.COMMA:
                return
            elif isinstance(arg, Node) and arg.type == syms.argument:
                # keyword argument
                name, equal, value = arg.children
                assert name.type == token.NAME # what is the symbol for 1?
                assert equal.type == token.EQUAL # what is the symbol for 1?
                value = value.clone()
                value.prefix = " "
                kwargs[name.value] = value
            else:
                assert not kwargs, 'all positional args are assumed to come first'
                posargs.append(arg.clone())

        func = results['func'].value

        custom_helper = False

        if node.parent.type == syms.return_stmt:
            # custom helper with `return eq_(...)`
            # We're not rendering the `assert` in that case
            # to allow the code to continue functioning
            custom_helper = True

        posargs = []
        kwargs = []

        if results['arglist'].type == syms.arglist:
            for arg in results['arglist'].children:
                process_arg(arg)
        else:
            process_arg(results['arglist'])

        if len(posargs) == 2:
            left, right = posargs
        elif len(posargs) == 3:
            left, right, _ = posargs

        left.prefix = " "
        right.prefix = " "

        strip_newlines(left)
        strip_newlines(right)

        # Ignore customized assert messages for now
        if isinstance(right, Leaf) and right.value in ('None', 'True', 'False'):
            op = Name('is', prefix=' ')
            body = [Node(syms.comparison, (left, op, right))]
        else:
            op = Name('==', prefix=' ')
            body = [Node(syms.comparison, (left, op, right))]

        indent = find_indentation(node)

        ret = Name('assert')

        if node.parent.prefix.endswith(indent):
            ret.prefix = indent

        if custom_helper:
            return body

        return [ret] + body
