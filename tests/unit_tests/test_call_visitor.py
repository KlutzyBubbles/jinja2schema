# coding: utf-8
import pytest
from jinja2 import nodes

from jinja2schema.core import parse
from jinja2schema.exceptions import InvalidExpression
from jinja2schema.model import List, Dictionary, Scalar, Variable
from jinja2schema.visitors.expr import visit_call, Context


def get_scalar_context(node):
    return Context(return_struct_cls=Scalar, predicted_struct=Scalar.from_node(node))


def test_range_call():
    template = '{{ range(n) }}'
    node = parse(template).find(nodes.Call)

    rtype, struct = visit_call(node, Context(predicted_struct=Variable()))

    expected_rtype = List(Scalar())
    assert rtype == expected_rtype

    expected_struct = Dictionary({
        'n': Scalar(label='n', linenos=[1]),
    })
    assert struct == expected_struct


def test_lipsum_call():
    template = '{{ lipsum(n) }}'
    node = parse(template).find(nodes.Call)

    rtype, struct = visit_call(node, Context(predicted_struct=Variable()))

    expected_rtype = Scalar()
    assert rtype == expected_rtype

    expected_struct = Dictionary({
        'n': Scalar(label='n', linenos=[1]),  # TODO must be Scalar
    })
    assert struct == expected_struct


def test_dict_call():
    template = '''{{ dict(x=\ndict(\na=1, b=2), y=a) }}'''
    call_node = parse(template).find(nodes.Call)
    rtype, struct = visit_call(
        call_node, Context(predicted_struct=Variable.from_node(call_node)))

    expected_rtype = Dictionary({
        'x': Dictionary({
            'a': Scalar(linenos=[3], constant=True, value=1),
            'b': Scalar(linenos=[3], constant=True, value=2)
        }, linenos=[2], constant=True),
        'y': Variable(label='a', linenos=[3]),
    }, linenos=[1], constant=True)
    assert rtype == expected_rtype

    expected_struct = Dictionary({
        'a': Variable(label='a', linenos=[3]),
    })
    assert struct == expected_struct


def test_str_method_calls():
    template = '''{{ x.endswith(suffix) }}'''
    call_node = parse(template).find(nodes.Call)
    rtype, struct = visit_call(call_node, get_scalar_context(call_node))

    expected_rtype = Scalar()
    assert rtype == expected_rtype

    expected_struct = Dictionary({
        'x': Scalar(label='x', linenos=[1]),
        # TODO suffix must be in struct too
    })
    assert struct == expected_struct

    template = '''{{ x.split(separator) }}'''
    call_node = parse(template).find(nodes.Call)
    ctx = Context(return_struct_cls=Variable, predicted_struct=Variable.from_node(call_node))
    rtype, struct = visit_call(call_node, ctx)

    expected_rtype = List(Scalar())
    assert rtype == expected_rtype

    expected_struct = Dictionary({
        'x': Scalar(label='x', linenos=[1]),
        'separator': Scalar(label='separator', linenos=[1]),
    })
    assert struct == expected_struct



def test_raise_on_variable_call():
    for template in ('{{ x.some_variable_f() }}', '{{ xxx() }}'):
        call_node = parse(template).find(nodes.Call)
        with pytest.raises(InvalidExpression) as e:
            visit_call(call_node, get_scalar_context(call_node))
        assert 'call is not supported' in str(e.value)
