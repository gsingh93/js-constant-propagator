#!/usr/bin/env python2

import argparse
import sys

from slimit.parser import Parser
from slimit.visitors.nodevisitor import ASTVisitor
from slimit import ast


def type_name(root):
    return type(root).__name__


def is_const(node):
    return type_name(node) == 'Number' or type_name(node) == 'String'


class ConstantReductionVisitor(ASTVisitor):
    const_vars = {}
    const_arrs = {}
    indent = 0

    def __init__(self, debug):
        self.debug = debug

    def visit_node(self, node):
        children = node.children()
        for i in range(len(children)):
            if children[i] != None:
                children[i] = self.visit(children[i])

        return node

    def visit_identifier(self, node):
        if node.value in self.const_vars:
            return self.const_vars[node.value]

        return node

    def visit_string(self, node):
        node.value = node.value.decode('string_escape')
        return node

    def visit_bracketaccessor(self, node):
        node.expr = self.visit(node.expr)
        ident = node.node
        if self.debug:
            print self.indent * ' ' + type_name(ident)
        assert type_name(ident) == 'Identifier'

        if ident.value in self.const_arrs and is_const(node.expr):
            if node.expr.value in self.const_arrs[ident.value]:
                return self.const_arrs[ident.value][node.expr.value]
        return node

    def visit_vardecl(self, node):
        children = node.children()

        ident = node.identifier
        if self.debug:
            print self.indent * ' ' + type_name(ident)
        assert type_name(ident) == "Identifier"

        node.initializer = self.visit(node.initializer)
        init = node.initializer

        if type_name(init) != 'Array':
            if is_const(init):
                self.const_vars[ident.value] = init
            elif ident.value in self.const_vars:
                del const_vars[ident.value]
        else:
            d = {}
            i = 0
            for child in init.children():
                if is_const(child):
                    d[str(i)] = child
                i += 1
            self.const_arrs[ident.value] = d

        return node

    def visit_binop(self, node):
        node.left = self.visit(node.left)
        node.right = self.visit(node.right)

        if is_const(node.left) and is_const(node.right):
            op = node.op
            left = int(node.left.value)
            right = int(node.right.value)
            if op == '+':
                node = ast.Number(str(left + right))
            elif op == '-':
                node = ast.Number(str(left - right))
            elif op == '/':
                node = ast.Number(str(left / right))
            elif op == '*':
                node = ast.Number(str(left * right))

        return node

    def visit(self, root):
        self.indent += 1
        func = getattr(self, "visit_%s" % type_name(root).lower(), self.visit_node)
        if self.debug:
            print self.indent * ' ' + type_name(root)
        ret_val = func(root)
        self.indent -= 1
        return ret_val


def parse_args():
    parser = argparse.ArgumentParser(
        description='Apply constant folding and propagation to JavaScript files')
    parser.add_argument('filename', help='input JavaScript file')
    parser.add_argument('-d', '--debug', action='store_true', help='enable debugging output')

    return parser.parse_args(sys.argv[1:])


def main():
    args = parse_args()

    with open(args.filename) as f:
        source = f.read()

    parser = Parser()
    tree = parser.parse(source)

    visitor = ConstantReductionVisitor(args.debug)
    tree = visitor.visit(tree)
    print tree.to_ecma()


if __name__ == '__main__':
    main()
