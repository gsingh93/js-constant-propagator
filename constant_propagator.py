#!/usr/bin/env python2

import argparse
import sys

from slimit.parser import Parser
from slimit.visitors.nodevisitor import ASTVisitor
from slimit import ast


class JsType:
    NUMBER = 'Number'
    STRING = 'String'
    BOOL = 'Boolean'
    NULL = 'Null'
    UNDEFINED = 'Undefined' # TODO: Doesn't exist in slimit

    PRIMITIVES = [NUMBER, STRING, BOOL, NULL, UNDEFINED]


class NodeType:
    IDENTIFIER = 'Identifier'
    BRACKET_ACCESSOR = 'BracketAccessor'
    ARRAY = 'Array'


ast.Node.name = lambda self: type(self).__name__
ast.Node.is_const = lambda self: self.name() in JsType.PRIMITIVES


def print_indented(indent, node):
    print indent * ' ' + node.name()


class ConstantReductionVisitor(ASTVisitor):
    const_vars = {}
    const_arrs = {}
    indent = 0

    def __init__(self, debug=False):
        self.debug = debug

    def visit_attrs(self, node, *attrs):
        if node is None:
            return None

        for attr_name in attrs:
            if not hasattr(node, attr_name):
                raise Exception("Property %s doesn't exist on node type %s"
                                % (attr_name, node.name()))
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

    def visit_identifier(self, node, modifying):
        if node.value in self.const_vars:
            if modifying:
                del self.const_vars[node.value]
            else:
                return self.const_vars[node.value]

        return node

    def visit_string(self, node):
        node.value = node.value.decode('string_escape')
        return node

    def visit_number(self, node):
        return node

    def visit_assign(self, node):
        node.left = self.visit(node.left, True)
        tname = node.left.name()
        assert tname in [NodeType.IDENTIFIER, NodeType.BRACKET_ACCESSOR] #TODO: Property
        node.right = self.visit(node.right)
        if tname == NodeType.IDENTIFIER:
            ident = node.left
            if node.right.name() == NodeType.IDENTIFIER:
                if node.right.value in self.const_arrs:
                    d = self.const_arrs[node.right.value]
                    self.const_arrs[ident.value] = d
            if node.right.is_const():
                self.const_vars[ident.value] = node.right
            elif node.left.value in self.const_vars:
                del self.const_vars[ident.value]
        else:
            assert tname == NodeType.BRACKET_ACCESSOR
            ident = node.left.node
            index = node.left.expr
            if node.right.is_const():
                self.const_arrs[ident.value][index.value] = node.right
            elif index.value in self.const_arrs[ident.value]:
                del self.const_arrs[ident.value][index.value]

        return node

    def visit_object(self, node):
        return self.visit_attrs(node, 'properties')

    def visit_varstatement(self, node):
        return self.visit_node(node)

    def visit_block(self, node):
        return self.visit_node(node)

    def visit_bracketaccessor(self, node, modifying):
        ident = node.node
        if self.debug:
            print_indented(self.indent + 1, ident)
        node.expr = self.visit(node.expr)

        if ident.name() == NodeType.IDENTIFIER:
            if ident.value in self.const_arrs and node.expr.is_const():
                if node.expr.value in self.const_arrs[ident.value]:
                    if modifying:
                        del self.const_arrs[ident.value][node.expr.value]
                    else:
                        return self.const_arrs[ident.value][node.expr.value]
        else:
            node.node = self.visit(node.node)

        return node

    def visit_with(self, node):
        return self.visit_attrs(node, 'expr', 'statement')

    def visit_switch(self, node):
        return self.visit_attrs(node, 'expr', 'cases', 'default')

    def visit_case(self, node):
        return self.visit_attrs(node, 'expr', 'elements')

    def visit_default(self, node):
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
        assert ident.name() == NodeType.IDENTIFIER

        node.initializer = self.visit(node.initializer)
        init = node.initializer

        if init.name() != NodeType.ARRAY:
            if init.is_const():
                self.const_vars[ident.value] = init
            elif ident.value in self.const_vars:
                del self.const_vars[ident.value] # TODO: WTF, this wasn't tested
        else:
            d = {}
            i = 0
            for child in init.children():
                if child.is_const():
                    d[str(i)] = child
                i += 1
            self.const_arrs[ident.value] = d

        return node

    def visit_program(self, node):
        return self.visit_node(node)

    def visit_unaryop(self, node):
        if node.op in ['++', '--']:
            node.value = self.visit(node.value, True)
            return node
        else:
            return self.visit_attrs(node, 'op', 'value', 'postfix')

    def visit_binop(self, node):
        node.left = self.visit(node.left)
        node.right = self.visit(node.right)

        # TODO: Check if all ops work the same way as JS
        # TODO: Check the integer to double conversions
        if node.left.is_const() and node.right.is_const():
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
            elif op == '&':
                node = ast.Number(str(left & right))
            elif op == '>>':
                node = ast.Number(str(left >> right))
            elif op == '<<':
                node = ast.Number(str(left << right))
            elif op == '>>>':
                node = ast.Number(str(left >> right))

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

    def visit_boolean(self, node):
        return node

    def visit(self, root, modifying=False):
        if root is None:
            return None

        lvalue = False
        tn = root.name()
        if tn in [NodeType.IDENTIFIER, NodeType.BRACKET_ACCESSOR]:
            lvalue = True

        tn = tn.lower()

        self.indent += 1
        func = getattr(self, 'visit_%s' % tn, None)
        if func is None:
            raise Exception('No visitor method defined for type ' + root.name())
        if self.debug:
            print_indented(self.indent, root)
        if lvalue:
            ret_val = func(root, modifying)
        else:
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
