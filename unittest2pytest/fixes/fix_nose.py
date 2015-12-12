# -*- coding: utf-8 -*-
from lib2to3.fixer_base import BaseFix
from lib2to3.fixer_util import (
    Comma, Name, Call, Node, Leaf,
    Newline, KeywordArg, find_indentation,
    ArgList, String, Number, syms, token)

from functools import partial
import re
import unittest


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

        posargs = []
        kwargs = []

        if results['arglist'].type == syms.arglist:
            for arg in results['arglist'].children:
                process_arg(arg)
        else:
            process_arg(results['arglist'])

        if len(posargs) == 2:
            left, right = posargs
            left.prefix = " "
            right.prefix = " "

            if right.value in ('None', 'True', 'False'):
                op = Name('is', prefix=' ')
                body = [Node(syms.comparison, (left, op, right))]
            else:
                op = Name('==', prefix=' ')
                body = [Node(syms.comparison, (left, op, right))]

        indent = find_indentation(node)

        ret = Name('assert')

        if node.parent.prefix.endswith(indent):
            ret.prefix = indent

        return [ret] + body
