# coding: utf-8
import pytest
from jinja2 import nodes
from jinja2schema.config import Config

from jinja2schema.core import infer
from jinja2schema.exceptions import MergeException, UnexpectedExpression
from jinja2schema.model import List, Dictionary, Scalar, Tuple, Variable


def test_basics_1():
    template = '''
    {% set d = {'x': 123, a: z.qwerty} %}
    {{ d.x }}
    '''
    struct = infer(template)
    expected_struct = Dictionary({
        'a': Scalar(label='a', linenos=[2]),
        'd': Dictionary(label='d', data={
            'x': Scalar(label='x', linenos=[2, 3]),
        }, linenos=[2, 3]),
        'z': Dictionary(label='z', data={
            'qwerty': Variable(label='qwerty', linenos=[2]),
        }, linenos=[2]),
    })
    assert struct == expected_struct

    template = '''
    {% set d = {'x': 123, a: z.qwerty} %}
    {{ d.x.field }}
    '''
    with pytest.raises(MergeException):
        infer(template)

    template = '''
    {% set x = '123' %}
    {{ x.test }}
    '''
    with pytest.raises(MergeException):
        infer(template)

    template = '''
    {% set a = {'x': 123} %}
    {% set b = {a: 'test'} %}
    '''
    with pytest.raises(MergeException):
        test = infer(template)

def test_basics_2():
    template = '''
    {% if test1 %}
        {% if test2 %}
            {% set d = {'x': 123, a: z.qwerty} %}
        {% else %}
            {% set d = {'x': 456, a: z.gsom} %}
        {% endif %}
    {% endif %}
    {% if d %}
        {{ d.x }}
    {% endif %}
    {{ z.gsom }}
    '''
    struct = infer(template)
    expected_struct = Dictionary({
        'a': Scalar(label='a', linenos=[4, 6]),
        'd': Dictionary(data={
          'x': Scalar(label='x', linenos=[4, 6, 10])
        }, label='d', linenos=[4, 6, 9, 10]),
        'test1': Variable(label='test1', linenos=[2]),
        'test2': Variable(label='test2', linenos=[3]),
        'z': Dictionary(data={
            'qwerty': Variable(label='qwerty', linenos=[4]),
            'gsom': Scalar(label='gsom', linenos=[6, 12]),
        }, label='z', linenos=[4, 6, 12]),
    })
    assert struct == expected_struct


def test_basics_3():
    template = '''
    {% if x %}
        {% set x = '123' %}
    {% else %}
        {% set x = '456' %}
    {% endif %}
    {{ x }}
    '''
    struct = infer(template)
    expected_struct = Dictionary({
        'x': Scalar(label='x', linenos=[2, 3, 5, 7]),
    })
    assert struct == expected_struct

    template = '''
    {% if z %}
        {% set x = '123' %}
    {% else %}
        {% set x = '456' %}
    {% endif %}
    {{ x }}
    '''
    struct = infer(template)
    expected_struct = Dictionary({
        'x': Scalar(label='x', linenos=[3, 5, 7]),
        'z': Variable(label='z', linenos=[2]),
    })
    assert struct == expected_struct

def test_basics_4():
    template = '''
    {% set xys = [
        ('a', 0.3),
        ('b', 0.3),
    ] %}
    {% if configuration is undefined %}
        {% set configuration = 'prefix-' ~ timestamp %}
    {% endif %}
    queue: {{ queue if queue is defined else 'wizard' }}
    description: >-
    {% for x, y in xys %}
        {{ loop.index }}:
        {{ x }} {{ y }}
    {% endfor %}
    '''
    struct = infer(template)
    expected_struct = Dictionary({
        'configuration': Scalar(label='configuration',
                                may_be_defined=True, checked_as_undefined=True, constant=False, linenos=[6, 7]),
        'queue': Scalar(label='queue', checked_as_defined=True, constant=False, linenos=[9]),
        'timestamp': Scalar(label='timestamp', constant=False, linenos=[7]),
        'xys': List(Tuple([Scalar(label='x', linenos=[3, 4, 13]), Scalar(label='y', linenos=[3, 4, 13])], linenos=[3, 4, 11]), label='xys', constant=False, linenos=[2, 11])
    })
    assert struct == expected_struct


def test_basics_5():
    template = '''
    {% for row in items|batch(3, '&nbsp;') %}
        {% for column in row %}
            {{ column.x }}
        {% endfor %}
    {% endfor %}
    '''
    struct = infer(template)
    expected_struct = Dictionary({
        'column': Dictionary({
            'x': Scalar(label='x', linenos=[4])
        }, label='column', linenos=[4]),
        'items': List(List(Variable(), label='row', linenos=[2]), label='items', linenos=[2]),
        'row': List(Variable(label='column', linenos=[3]), label='row', linenos=[3])
    })
    assert struct == expected_struct


def test_basics_6():
    template = '''
    {% for row in items|batch(3, '&nbsp;') %}
    {% endfor %}
    '''
    struct = infer(template)
    expected_struct = Dictionary({
        'items': List(List(Variable(), label='row', linenos=[2]), label='items', linenos=[2]),
    })
    assert struct == expected_struct


def test_basics_7():
    template = '''
    {% for row in items|batch(3, '&nbsp;')|batch(1) %}
        {{ row[1][1].name }}
    {% endfor %}
    '''
    struct = infer(template)
    expected_struct = Dictionary({
        'items': List(List(Variable(), label='row', linenos=[2]), label='items', linenos=[2]),
        'row': Variable(label='row', linenos=[3])
    })
    assert struct == expected_struct


def test_basics_8():
    template = '''
    {% for row in items|batch(3, '&nbsp;')|batch(1) %}
        {{ row[1].name }}
    {% endfor %}
    '''
    struct = infer(template)
    expected_struct = Dictionary({
        'items': List(List(Variable(), label='row', linenos=[2]), label='items', linenos=[2]),
        'row': Variable(label='row', linenos=[3])
    })
    print(struct)
    print(expected_struct)
    assert struct == expected_struct


def test_basics_9():
    template = '''
    {% set xs = items|batch(3, '&nbsp;') %}
    {{ xs[0][0] }}
    '''
    struct = infer(template)
    expected_struct = Dictionary({
        'items': List(List(Variable(), linenos=[2]), label='items', linenos=[2]),
        'xs': List(List(Variable(), linenos=[2]), label='xs', linenos=[2, 3])
    })
    assert struct == expected_struct


def test_basics_10():
    template = '''
    {% set items = data|dictsort %}
    {% for x, y in items %}
    {% endfor %}
    '''
    struct = infer(template)
    expected_struct = Dictionary({
        'data': Dictionary({}, label='data', linenos=[2]),
    })
    assert struct == expected_struct


def test_basics_11():
    template = '''
    {{ a|xmlattr }}
    {{ a.attr1|join(',') }}
    {{ a.attr2|default([])|first }}
    {{ a.attr3|default('gsom') }}
    {% for x in xs|rejectattr('is_active') %}
        {{ x }}
    {% endfor %}
    '''
    struct = infer(template)
    expected_struct = Dictionary({
        'a': Dictionary({
            'attr1': List(Scalar(), label='attr1', linenos=[3]),
            'attr2': List(Scalar(linenos=[4]), label='attr2', linenos=[4], used_with_default=True),
            'attr3': Scalar(label='attr3', linenos=[5], used_with_default=True, value='gsom')
        }, label='a', linenos=[2, 3, 4, 5]),
        'xs': List(
            Scalar(label='x', linenos=[7]),  # TODO it should be Dictionary({'is_active': Variable()})
            label='xs',
            linenos=[6]
        ),
    })
    assert struct == expected_struct


def test_basics_12():
    template = '''
    {% for k, v in data|dictsort %}
        {{ k }}
        {{ v }}
    {% endfor %}
    '''
    struct = infer(template)
    expected_struct = Dictionary({
        'data': Dictionary({}, label='data', linenos=[2]),
    })
    assert struct == expected_struct


def test_basics_13():
    config = Config()
    config.TYPE_OF_VARIABLE_INDEXED_WITH_INTEGER_TYPE = 'tuple'

    template = '''
    {% for x in xs %}
        {{ x[2] }}
        {{ x[3] }}
    {% endfor %}
    '''
    struct = infer(template, config)
    expected_struct = Dictionary({
        'xs': List(Tuple((
            Variable(label=None, linenos=[]),
            Variable(label=None, linenos=[]),
            Scalar(label=None, linenos=[3]),
            Scalar(label=None, linenos=[4]),
        ), label='x', linenos=[3, 4]), label='xs', linenos=[2])
    })
    assert struct == expected_struct


def test_basics_14():
    template = '''
    {{ section.FILTERS.test }}
    {%- for f in section.FILTERS.keys() %}
        {{ section.GEO }}
        {{ loop.index }}
    {%- endfor %}
    '''
    struct = infer(template)
    expected_struct = Dictionary({
        'section': Dictionary({
            'FILTERS': Dictionary({
                'test': Scalar(label='test', linenos=[2])
            }, label='FILTERS', linenos=[2, 3]),
            'GEO': Scalar(label='GEO', linenos=[4]),
        }, label='section', linenos=[2, 3, 4])
    })
    assert struct == expected_struct


def test_raw():
    template = '''
    {% raw %}
        {{ x }}
    {% endraw %}
    '''
    struct = infer(template)
    expected_struct = Dictionary()
    assert struct == expected_struct


def test_for():
    template = '''
    {% for number in range(10 - users|length) %}
        {{ number }}
    {% endfor %}
    '''
    struct = infer(template)
    expected_struct = Dictionary({
        'users': List(Variable(), label='users', linenos=[2]),
    })
    assert struct == expected_struct

    template = '''
    {% for number in range(10 - users|length) %}
        {{ number.field }}
    {% endfor %}
    '''
    with pytest.raises(MergeException):
        infer(template)

    template = '{{ range(10 - users|length) }}'
    with pytest.raises(UnexpectedExpression):
        infer(template)

    template = '''
    {% for number in lipsum(n=10) %}
    {% endfor %}
    '''
    with pytest.raises(UnexpectedExpression):
        infer(template)

    template = '''
    {% for k, v in data|dictsort %}
        {{ k.x }}
        {{ v }}
    {% endfor %}
    '''
    with pytest.raises(UnexpectedExpression):
        infer(template)


def test_assignment():
    template = '''
    {% set args = ['foo'] if foo else [] %}
    {% set args = args + ['bar'] %}
    {% set args = args + (['zork'] if zork else []) %}
    f({{ args|join(sep) }});
    '''
    struct = infer(template)
    expected_struct = Dictionary({
        'foo': Variable(label='foo', linenos=[2]),
        'zork': Variable(label='zork', linenos=[4]),
        'sep': Scalar(label='sep', linenos=[5])
    })
    assert struct == expected_struct


def test_boolean_conditions_setting_1():
    template = '''
    {% if x %}
        Hello!
    {% endif %}
    {{ 'Hello!' if y else '' }}
    '''
    config_1 = Config()
    struct = infer(template, config_1)
    expected_struct = Dictionary({
        'x': Variable(label='x', linenos=[2]),
        'y': Variable(label='y', linenos=[5]),
    })
    assert struct == expected_struct

    infer('{% if [] %}{% endif %}', config_1)  # make sure it doesn't raise

    config_2 = Config(BOOLEAN_CONDITIONS=True)
    struct = infer(template, config_2)
    expected_struct = Dictionary({
        'x': Scalar(label='x', linenos=[2]),
        'y': Scalar(label='y', linenos=[5]),
    })
    assert struct == expected_struct

    with pytest.raises(UnexpectedExpression) as e:
        infer('{% if [] %}{% endif %}', config_2)  # make sure this does raise
    assert str(e.value) == ('conflict on the line 1\n'
                            'got: NODE node jinja2.nodes.List of structure [<variable>]\n'
                            'expected structure: <boolean>')


def test_boolean_conditions_setting_2():
    config = Config(BOOLEAN_CONDITIONS=True)

    template = '''
    {% if x == 'test' %}
        Hello!
    {% endif %}
    '''
    struct = infer(template, config)
    expected_struct = Dictionary({
        'x': Variable(label='x', linenos=[2]),
    })
    assert struct == expected_struct

def test_block_1():
    config = Config()

    template = '''
        {% block test %}
            {{ x }}
            {{ y }}
        {% endblock %}
    '''
    struct = infer(template, config)
    expected_struct = Dictionary({
        'x': Scalar(label='x', linenos=[3]),
        'y':  Scalar(label='y', linenos=[4]),
    })
    assert struct == expected_struct
