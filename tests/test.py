import os
#import nose
from nose.plugins.skip import SkipTest
from slimit.parser import Parser
from constant_propagator import ConstantReductionVisitor


files = [
    'nested_array_index',
    'constant_variables',
    'constant_array',
    'constant_properties',
    'function_calls',
    'references',
    'binop.js',
]


def check_expected_output(filename):
    input_file = 'js/%s.js' % filename
    expect_file = input_file + '.expect'
    if not os.path.exists(expect_file):
        raise SkipTest('No expect file for test ' + filename)
    with open(input_file) as f, open(expect_file) as g:
        parser = Parser()
        tree = parser.parse(f.read())

        visitor = ConstantReductionVisitor()
        tree = visitor.visit(tree)
        js = tree.to_ecma().strip()

        expected_output = g.read().strip()
        if js != expected_output:
            print 'Expected:'
            print expected_output
            print ''
            print 'Got:'
            print js
            assert False


def test_files():
    for filename in files:
        yield check_expected_output, filename
