#!/usr/bin/env python2

import argparse
import sys

from slimit.parser import Parser
from slimit.visitors.nodevisitor import ASTVisitor
from slimit import ast


def print_indented(indent, node):
    print indent * ' ' + type_name(node)


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

    def visit_attrs(self, node, *attrs):
        if node is None:
            return None

        for attr_name in attrs:
            if not hasattr(node, attr_name):
                raise Exception("Property %s doesn't exist on node type %s"
                                % (attr_name, type_name(node)))
            attr = getattr(node, attr_name, None)
            if isinstance(attr, list):
                for i in range(len(attr)):
                    attr[i] = self.visit(attr[i])
            elif isinstance(attr, ast.Node):
                attr = self.visit(attr)
            else:
                continue

            setattr(node, attr_name, attr)

        return node

    def visit_array(self, node):
        return self.visit_attrs(node, 'items')

    def visit_regex(self, node):
        return node

    def visit_node(self, node):
        return self.visit_attrs(node, '_children_list')

    def visit_functioncall(self, node):
        return self.visit_attrs(node, 'identifier', 'args')

    def visit_newexpr(self, node):
        return self.visit_attrs(node, 'identifier', 'args')

    def visit_dotaccessor(self, node):
        return self.visit_attrs(node, 'node', 'identifier')

    def visit_return(self, node):
        return self.visit_attrs(node, 'expr')

    def visit_identifier(self, node):
        if node.value in self.const_vars:
            return self.const_vars[node.value]

        return node

    def visit_string(self, node):
        node.value = node.value.decode('string_escape')
        return node

    def visit_number(self, node):
        return node

    def visit_assign(self, node):
        return self.visit_attrs(node, 'op', 'left', 'right')

    def visit_object(self, node):
        return self.visit_attrs(node, 'properties')

    def visit_varstatement(self, node):
        return self.visit_node(node)

    def visit_block(self, node):
        return self.visit_node(node)

    def visit_bracketaccessor(self, node):
        ident = node.node
        if self.debug:
            print_indented(self.indent + 1, ident)
        node.expr = self.visit(node.expr)

        if type_name(ident) == 'Identifier':
            if ident.value in self.const_arrs and is_const(node.expr):
                if node.expr.value in self.const_arrs[ident.value]:
                    return self.const_arrs[ident.value][node.expr.value]

        return node

    def visit_with(self, node):
        return self.visit_attrs(node, 'expr', 'statement')

    def visit_switch(self, node):
        return self.visit_attrs(node, 'expr', 'cases', 'default')

    def visit_case(self, node):
        return self.visit_attrs(node, 'expr', 'elements')

    def visit_defaults(self, node):
        return self.visit_attrs(node, 'elements')

    def visit_label(self, node):
        return self.visit_attrs(node, 'identifier', 'statement')

    def visit_throw(self, node):
        return self.visit_attrs(node, 'expr')

    def visit_try(self, node):
        return self.visit_attrs(node, 'statements', 'catch', 'fin')

    def visit_catch(self, node):
        return self.visit_attrs(node, 'identifier', 'elements')

    def visit_finally(self, node):
        return self.visit_attrs(node, 'elements')

    def visit_funcbase(self, node):
        return self.visit_attrs(node, 'identifier', 'parameters', 'elements')

    def visit_funcdecl(self, node):
        return self.visit_funcbase(node)

    def visit_funcexpr(self, node):
        return self.visit_funcbase(node)

    def visit_comma(self, node):
        return self.visit_attrs(node, 'left', 'right')

    def visit_emptystatement(self, node):
        return node

    def visit_exprstatement(self, node):
        return self.visit_attrs(node, 'expr')

    def visit_ellision(self, node):
        return node

    def visit_this(self, node):
        return node

    def visit_vardecl(self, node):
        children = node.children()

        ident = node.identifier
        if self.debug:
            print_indented(self.indent + 1, ident)
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

    def visit_program(self, node):
        return self.visit_node(node)

    def visit_unaryop(self, node):
        return self.visit_attrs(node, 'op', 'value', 'postfix')

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

    def visit_conditional(self, node):
        return self.visit_attrs(node, 'predicate', 'consequent', 'alternative')

    def visit_if(self, node):
        return self.visit_attrs(node, 'predicate', 'consequent', 'alternative')

    def visit_dowhile(self, node):
        return self.visit_attrs(node, 'predicate', 'statement')

    def visit_while(self, node):
        return self.visit_attrs(node, 'predicate', 'statement')

    def visit_for(self, node):
        return self.visit_attrs(node, 'init', 'cond', 'count', 'statement')

    def visit_forin(self, node):
        return self.visit_attrs(node, 'item', 'iterable', 'statement')

    def visit_continue(self, node):
        return self.visit_attrs(node, 'identifier')

    def visit_break(self, node):
        return self.visit_attrs(node, 'identifier')

    def visit_null(self, node):
        return node

    def visit(self, root):
        if root is None:
            return None

        self.indent += 1
        func = getattr(self, "visit_%s" % type_name(root).lower(), None)
        if func is None:
            raise Exception('No visitor method defined for type ' + type_name(root))
        if self.debug:
            print_indented(self.indent, root)
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
