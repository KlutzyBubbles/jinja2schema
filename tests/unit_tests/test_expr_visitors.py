# coding: utf-8
from jinja2 import nodes
import pytest
from jinja2schema import InvalidExpression

from jinja2schema.config import Config
from jinja2schema.core import parse
from jinja2schema.visitors.expr import (Context, visit_getitem, visit_cond_expr, visit_test,
                                        visit_getattr, visit_compare, visit_const)
from jinja2schema.model import Dictionary, Scalar, List, Variable, Tuple


def get_scalar_context(node):
    return Context(return_struct_cls=Scalar, predicted_struct=Scalar.from_node(node))


def test_cond_expr():
    template = '''{{ queue if queue is defined else 'wizard' }}''',
    node = parse(template).find(nodes.CondExpr)
    rtype, struct = visit_cond_expr(node, get_scalar_context(node))

    expected_struct = Dictionary({
        'queue': Scalar(label='queue', linenos=[1], checked_as_defined=True)
    })
    assert struct == expected_struct

    template = '''{{ queue if queue is undefined else 'wizard' }}'''
    node = parse(template).find(nodes.CondExpr)
    rtype, struct = visit_cond_expr(node, get_scalar_context(node))

    expected_struct = Dictionary({
        'queue': Scalar(label='queue', linenos=[1])
    })
    assert struct == expected_struct


def test_getattr_1():
    template = '{{ (x or y).field.subfield[2].a }}'
    node = parse(template).find(nodes.Getattr)
    rtype, struct = visit_getattr(node, get_scalar_context(node))

    x_or_y_dict = {
        'field': Dictionary({
            'subfield': List(Dictionary({
                'a': Scalar(label='a', linenos=[1])
            }, linenos=[1]), label='subfield', linenos=[1]),
        }, label='field', linenos=[1]),
    }

    expected_struct = Dictionary({
        'x': Dictionary(x_or_y_dict, label='x', linenos=[1]),
        'y': Dictionary(x_or_y_dict, label='y', linenos=[1])
    })
    assert struct == expected_struct


def test_getattr_2():
    template = '{{ data.field.subfield }}'
    node = parse(template).find(nodes.Getattr)
    rtype, struct = visit_getattr(node, get_scalar_context(node))

    expected_struct = Dictionary({
        'data': Dictionary({
            'field': Dictionary({
                'subfield': Scalar(label='subfield', linenos=[1]),
            }, label='field', linenos=[1]),
        }, label='data', linenos=[1]),
    })
    assert struct == expected_struct


def test_getattr_3():
    template = '''{{ a[z][1:\nn][1].x }}'''
    node = parse(template).find(nodes.Getattr)
    config = Config()
    config.TYPE_OF_VARIABLE_INDEXED_WITH_VARIABLE_TYPE = 'list'
    rtype, struct = visit_getattr(node, get_scalar_context(node), {}, config)

    expected_struct = Dictionary({
        'a': List(
            List(
                List(
                    Dictionary({
                        'x': Scalar(label='x', linenos=[2])
                    }, linenos=[2]),
                    linenos=[2]),
                linenos=[1]
            ),
            label='a',
            linenos=[1]
        ),
        'z': Scalar(label='z', linenos=[1]),
        'n': Scalar(label='n', linenos=[2])
    })
    assert struct == expected_struct


def test_getitem_1():
    template = '''{{ a['b']['c'][1]['d'][x] }}'''
    node = parse(template).find(nodes.Getitem)
    config = Config()
    config.TYPE_OF_VARIABLE_INDEXED_WITH_VARIABLE_TYPE = 'list'
    rtype, struct = visit_getitem(node, get_scalar_context(node), {}, config)

    expected_struct = Dictionary({
        'a': Dictionary({
            'b': Dictionary({
                'c': List(Dictionary({
                    'd': List(Scalar(linenos=[1]), label='d', linenos=[1])
                }, linenos=[1]), label='c', linenos=[1]),
            }, label='b', linenos=[1]),
        }, label='a', linenos=[1]),
        'x': Scalar(label='x', linenos=[1]),
    })
    assert struct == expected_struct


def test_getitem_2():
    template = '''{{ a[z] }}'''
    node = parse(template).find(nodes.Getitem)
    config = Config()
    config.TYPE_OF_VARIABLE_INDEXED_WITH_VARIABLE_TYPE = 'dictionary'
    rtype, struct = visit_getitem(node, get_scalar_context(node), {}, config)

    expected_struct = Dictionary({
        'a': Dictionary(label='a', linenos=[1]),
        'z': Scalar(label='z', linenos=[1]),
    })
    assert struct == expected_struct


def test_getitem_3():
    template = '''{{ a[3] }}'''
    node = parse(template).find(nodes.Getitem)
    config = Config()
    config.TYPE_OF_VARIABLE_INDEXED_WITH_INTEGER_TYPE = 'tuple'
    rtype, struct = visit_getitem(node, get_scalar_context(node), {}, config)

    expected_struct = Dictionary({
        'a': Tuple([
            Variable(),
            Variable(),
            Variable(),
            Scalar(linenos=[1]),
        ], label='a', linenos=[1]),
    })
    assert struct == expected_struct


def test_compare_1():
    template = '{{ a < b < c }}'
    node = parse(template).find(nodes.Compare)
    rtype, struct = visit_compare(node, get_scalar_context(node))

    expected_struct = Dictionary({
        'a': Variable(label='a', linenos=[1]),
        'b': Variable(label='b', linenos=[1]),
        'c': Variable(label='c', linenos=[1]),
    })
    assert struct == expected_struct


def test_compare_2():
    template = '{{ a + b[1] - c == 4 == x }}'
    node = parse(template).find(nodes.Compare)
    rtype, struct = visit_compare(node, get_scalar_context(node))
    # TODO make customizable
    expected_struct = Dictionary({
        'a': Variable(label='a', linenos=[1]),
        'b': List(Variable(linenos=[1]), label='b', linenos=[1]),
        'c': Variable(label='c', linenos=[1]),
        'x': Variable(label='x', linenos=[1]),
    })
    assert struct == expected_struct


def test_slice():
    template = '''{{ xs[a:2:b] }}'''
    node = parse(template).find(nodes.Getitem)
    rtype, struct = visit_getitem(node, get_scalar_context(node))
    assert struct == Dictionary({
        'xs': List(Scalar(linenos=[1]), label='xs', linenos=[1]),
        'a': Scalar(label='a', linenos=[1]),
        'b': Scalar(label='b', linenos=[1]),
    })


def test_test_1():
    template = '''{{ x is divisibleby (data.field) }}'''
    node = parse(template).find(nodes.Test)
    rtype, struct = visit_test(node, get_scalar_context(node))

    expected_struct = Dictionary({
        'x': Scalar(label='x', linenos=[1]),
        'data': Dictionary({
            'field': Scalar(label='field', linenos=[1]),
        }, label='data', linenos=[1])
    })

    assert struct == expected_struct

    template = '''{{ x is divisibleby 3 }}'''
    node = parse(template).find(nodes.Test)
    rtype, struct = visit_test(node, get_scalar_context(node))

    expected_struct = Dictionary({
        'x': Scalar(label='x', linenos=[1]),
    })
    assert struct == expected_struct


def test_test_2():
    template = '''{{ x is string }}'''
    node = parse(template).find(nodes.Test)
    rtype, struct = visit_test(node, get_scalar_context(node))

    expected_struct = Dictionary({
        'x': Variable(label='x', linenos=[1])
    })
    assert struct == expected_struct

    template = '{{ x is variable_filter }}'
    node = parse(template).find(nodes.Test)
    with pytest.raises(InvalidExpression) as e:
        visit_test(node, get_scalar_context(node))
    assert 'line 1: variable test "variable_filter"' in str(e.value)


def test_compare():
    template = '''{{ a < c }}'''
    compare_node = parse(template).find(nodes.Compare)
    rtype, struct = visit_compare(compare_node, get_scalar_context(compare_node))
    expected_rtype = Scalar(linenos=[1])
    assert rtype == expected_rtype


def test_const():
    template = '''{{ false }}'''
    const_node = parse(template).find(nodes.Const)
    rtype, struct = visit_const(const_node, get_scalar_context(const_node))
    assert rtype == Scalar(constant=True, linenos=[1], value=False)
