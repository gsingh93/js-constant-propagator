import nose
from slimit.parser import Parser
from constant_propagator import ConstantReductionVisitor


files = [
    'nested_array_index',
    'constant_variables',
    'constant_array',
]


def check_expected_output(filename):
    input_file = 'js/%s.js' % filename
    expect_file = input_file + '.expect'
    with open(input_file) as f, open(expect_file) as g:
        parser = Parser()
        tree = parser.parse(f.read())

        visitor = ConstantReductionVisitor()
        tree = visitor.visit(tree)
        js = tree.to_ecma()

        assert js.strip() == g.read().strip()


def test_files():
    for filename in files:
        yield check_expected_output, filename
