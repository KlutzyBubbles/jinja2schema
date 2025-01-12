# coding: utf-8
import pytest
from jinja2 import nodes

from jinja2schema.core import parse, infer_from_node
from jinja2schema.visitors.stmt import visit_assign, visit_if, visit_for
from jinja2schema.exceptions import MergeException, UnexpectedExpression
from jinja2schema.model import Dictionary, Scalar, List, Variable, Tuple


def test_for_1():
    template = '''
    {% for x in a.b %}
        {{ x }}
    {% endfor %}
    '''
    node = parse(template).find(nodes.For)
    struct = visit_for(node)
    expected_struct = Dictionary({
        'a': Dictionary({
            'b': List(Scalar(label='x', linenos=[3]), label='b', linenos=[2])
        }, label='a', linenos=[2]),
    })
    assert struct == expected_struct


def test_for_2():
    template = '''
    {% for x in xs %}
        {{ x }}
        {% for y in ys %}
            {{ loop.index0 }}
        {% endfor %}
        {{ loop.length }}
    {% endfor %}
    '''
    node = parse(template)
    struct = infer_from_node(node)

    expected_struct = Dictionary({
        'xs': List(Scalar(label='x', linenos=[3]), label='xs', linenos=[2]),
        'ys': List(Variable(linenos=[4]), label='ys', linenos=[4]),
    })
    assert struct == expected_struct


def test_for_3():
    template = '''
    {% for a, b in list %}
        {{ a.field }}
        {{ b }}
    {% endfor %}
    '''
    node = parse(template).find(nodes.For)
    struct = visit_for(node)

    expected_struct = Dictionary({
        'list': List(Tuple((
            Dictionary({
                'field': Scalar(label='field', linenos=[3])
            }, label='a', linenos=[3]),
            Scalar(label='b', linenos=[4])
        ), linenos=[2]), label='list', linenos=[2])
    })
    assert struct == expected_struct


def test_assign_1():
    template = '''{% set a = b %}'''
    node = parse(template).find(nodes.Assign)

    struct = visit_assign(node)
    expected_struct = Dictionary({
        'a': Variable(label='a', linenos=[1], constant=True),
        'b': Variable(label='b', linenos=[1]),
    })
    assert struct == expected_struct


def test_assign_2():
    template = '''{% set y = "-" ~ y %}'''
    node = parse(template).find(nodes.Assign)

    struct = visit_assign(node)
    expected_struct = Dictionary({
        'y': Scalar(label='y', linenos=[1])
    })
    assert struct == expected_struct


def test_assign_3():
    template = '''{% set a, b = {'a': 1, 'b': 2} %}'''
    node = parse(template).find(nodes.Assign)
    with pytest.raises(UnexpectedExpression):
        visit_assign(node)


def test_assign_4():
    template = '''{% set a, b = 1, {'gsom': 'gsom', z: z} %}'''
    node = parse(template).find(nodes.Assign)

    struct = visit_assign(node)
    expected_struct = Dictionary({
        'a': Scalar(label='a', linenos=[1], constant=True, value=1),
        'b': Dictionary(data={
            'gsom': Scalar(linenos=[1], constant=True, value='gsom'),
        }, label='b', linenos=[1], constant=True),
        'z': Scalar(label='z', linenos=[1]),
    })
    assert struct == expected_struct


def test_assign_5():
    template = '''
    {%- set weights = [
        ('A', {'data': 0.3}),
        ('B', {'data': 0.9}),
    ] %}
    '''
    node = parse(template).find(nodes.Assign)
    struct = visit_assign(node)
    expected_struct = Dictionary({
        'weights': List(Tuple([
            Scalar(linenos=[3, 4], constant=True),
            Dictionary({
                'data': Scalar(linenos=[3, 4], constant=True)
            }, linenos=[3, 4], constant=True),
        ], linenos=[3, 4], constant=True), label='weights', linenos=[2], constant=True)
    })
    assert struct == expected_struct


def test_assign_6():
    template = '''
    {%- set weights = [
        ('A', {'data': 0.3}),
        ('B', {'data': 0.9}, 1, 2),
    ] %}
    '''
    node = parse(template).find(nodes.Assign)
    with pytest.raises(MergeException):
        visit_assign(node)


def test_if_1():
    template = '''
    {% if (x or y) and not z %}
        {{ x }}
        {{ z.field }}
    {% endif %}
    '''
    node = parse(template).find(nodes.If)
    struct = visit_if(node)

    expected_struct = Dictionary({
        'z': Dictionary({
            'field': Scalar(label='field', linenos=[4]),
        }, label='z', linenos=[2, 4]),
        'x': Scalar(label='x', linenos=[2, 3]),
        'y': Variable(label='y', linenos=[2]),
    })
    assert struct == expected_struct


def test_if_2():
    template = '''
    {% if z > x > y %}
    {% endif %}
    {% if x == y and x == 'asd' and z == 5 %}
    {% endif %}
    {{ x }}
    '''
    struct = infer_from_node(parse(template))
    expected_struct = Dictionary({
        'x': Scalar(label='x', linenos=[2, 4, 6]),
        'y': Variable(label='y', linenos=[2, 4]),
        'z': Variable(label='z', linenos=[2, 4]),
    })
    assert struct == expected_struct