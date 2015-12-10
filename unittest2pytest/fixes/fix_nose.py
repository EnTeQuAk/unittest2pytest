# -*- coding: utf-8 -*-
from lib2to3.fixer_base import BaseFix
from lib2to3.fixer_util import (
    Comma, Name, Call, Node, Leaf,
    Newline, KeywordArg, find_indentation,
    ArgList, String, Number, syms, token)

from functools import partial
import re
import unittest

from .. import utils


TEMPLATE_PATTERN = re.compile('[\1\2]|[^\1\2]+')

def CompOp(op, left, right, kws):
    op = Name(op, prefix=" ")
    left.prefix = ""
    right.prefix = " "

    if getattr(right, 'value', '') in ('None', 'True', 'False') and op.value == '==':
        return CompOp('is', left, right, kws)

    return Node(syms.comparison, (left, op, right))


def fill_template(template, *args):
    parts = TEMPLATE_PATTERN.findall(template)
    kids = []
    for p in parts:
        if p == '':
            continue
        elif p in '\1\2\3\4\5':
            p = args[ord(p)-1]
            p.prefix = ''
        else:
            p = Name(p)
        kids.append(p)
    return kids

def DualOp(template, first, second, kws):
    kids = fill_template(template, first, second)
    return Node(syms.test, kids, prefix=" ")


def UnaryOp(prefix, postfix, value, kws):
    kids = []
    if prefix:
        kids.append(Name(prefix))
    value.prefix = " "
    kids.append(value)
    if postfix:
        kids.append(Name(postfix))
    return Node(syms.test, kids)


_method_map = {
    # simple ones
    'eq_':         partial(DualOp, 're.search(\1, \2)'),
#    'ok_':         partial(UnaryOp, '', ''),
}


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

        method = results['func'].value

        posargs = []
        kwargs = {}

        # This is either a "arglist" or a single argument
        if results['arglist'].type == syms.arglist:
            for arg in results['arglist'].children:
                process_arg(arg)
        else:
            process_arg(results['arglist'])

        import nose.tools

        test_func = getattr(nose.tools, method)

        required_args, argsdict = utils.resolve_func_args(test_func, posargs, kwargs)

        replacement = [Name('assert'), _method_map[method](*required_args, kws=argsdict)]

        if results['arglist'].next_sibling and results['arglist'].next_sibling.type == token.NEWLINE:
            # The eq_ statement goes over multiple lines, wrap it in ()
            replacement.insert(1, Name(' ('))
            replacement.append(Name(')'))

        stmt = Node(syms.assert_stmt, replacement)

        if argsdict.get('msg', None) is not None:
            stmt.children.extend((Name(','), argsdict['msg']))
        stmt.prefix = node.prefix
        return stmt


print(FixNose.PATTERN)
