import pytest
from jinja2 import nodes

from jinja2schema import parse, UnexpectedExpression, InvalidExpression
from jinja2schema.visitors.expr import visit_filter, Context
from jinja2schema.model import Dictionary, Scalar, List, Unknown, String, Number
from jinja2schema.config import Config


def get_scalar_context(node):
    return Context(return_struct_cls=Scalar, predicted_struct=Scalar.from_node(node))


def test_string_filters():
    for filter in ('striptags', 'capitalize', 'title', 'upper', 'urlize'):
        template = '{{ x|' + filter + ' }}'
        node = parse(template).find(nodes.Filter)

        ctx = Context(return_struct_cls=Scalar, predicted_struct=Scalar.from_node(node))
        rtype, struct = visit_filter(node, ctx)

        expected_rtype = String(label='x', linenos=[1])
        expected_struct = Dictionary({
            'x': String(label='x', linenos=[1]),
        })
        assert rtype == expected_rtype
        assert struct == expected_struct


def test_batch_and_slice_filters():
    for filter in ('batch', 'slice'):
        template = '{{ items|' + filter + '(3, "&nbsp;") }}'
        node = parse(template).find(nodes.Filter)

        unknown_ctx = Context(predicted_struct=Unknown.from_node(node))
        rtype, struct = visit_filter(node, unknown_ctx)

        expected_rtype = List(List(Unknown(), linenos=[1]), linenos=[1])
        assert rtype == expected_rtype

        expected_struct = Dictionary({
            'items': List(Unknown(), label='items', linenos=[1]),
        })
        assert struct == expected_struct

        scalar_ctx = Context(predicted_struct=Scalar.from_node(node))
        with pytest.raises(UnexpectedExpression) as e:
            visit_filter(node, scalar_ctx)
        assert str(e.value) == ('conflict on the line 1\n'
                                'got: NODE node jinja2.nodes.Filter of structure [[<unknown>]]\n'
                                'expected structure: <scalar>')


def test_default_filter():
    template = '''{{ x|default('g') }}'''
    node = parse(template).find(nodes.Filter)
    rtype, struct = visit_filter(node, get_scalar_context(node))

    expected_struct = Dictionary({
        'x': String(label='x', linenos=[1], used_with_default=True, value='g'),
    })
    assert struct == expected_struct


def test_filter_chaining():
    template = '''{{ (xs|first|lnode).gsom|sort|length }}'''
    node = parse(template).find(nodes.Filter)
    rtype, struct = visit_filter(node, get_scalar_context(node))

    expected_struct = Dictionary({
        'xs': List(List(Dictionary({
            'gsom': List(Unknown(), label='gsom', linenos=[1]),
        }, linenos=[1]), linenos=[1]), label='xs', linenos=[1]),
    })
    assert struct == expected_struct

    template = '''{{ x|list|sort|first }}'''
    node = parse(template).find(nodes.Filter)
    rtype, struct = visit_filter(node, get_scalar_context(node))

    expected_struct = Dictionary({
        'x': Scalar(label='x', linenos=[1]),
    })
    assert struct == expected_struct

    template = '''{{ x|first|list }}'''
    node = parse(template).find(nodes.Filter)
    with pytest.raises(UnexpectedExpression):
        visit_filter(node, get_scalar_context(node))

def test_unknown_filter_ignore():
    config = Config(RAISE_ON_NO_FILTER=False)
    template = '''{{ x|unknownfilter }}'''
    node = parse(template).find(nodes.Filter)
    rtype, struct = visit_filter(node, get_scalar_context(node), config=config)
    expected_struct = Dictionary({
        'x': Unknown(label='x', linenos=[1]),
    })
    assert struct == expected_struct

    template = '''{{ x|unknownfilter(y) }}'''
    node = parse(template).find(nodes.Filter)
    rtype, struct = visit_filter(node, get_scalar_context(node), config=config)
    expected_struct = Dictionary({
        'x': Unknown(label='x', linenos=[1]),
        'y': Scalar(label='y', linenos=[1]),
    })
    assert struct == expected_struct

def test_custom_filter_ignore():
    def dummy_filter(value1, value2):
      return value2
    filters = [
      {
        'customfilter': dummy_filter
      }
    ]
    config = Config(CUSTOM_FILTERS=filters, RAISE_ON_NO_FILTER=True, RAISE_ON_INVALID_FILTER_ARGS=False)
    template = '''{{ x|customfilter }}'''
    node = parse(template).find(nodes.Filter)
    rtype, struct = visit_filter(node, get_scalar_context(node), config=config)
    expected_struct = Dictionary({
        'x': Unknown(label='x', linenos=[1]),
    })
    assert struct == expected_struct

    template = '''{{ x|customfilter(y) }}'''
    node = parse(template).find(nodes.Filter)
    rtype, struct = visit_filter(node, get_scalar_context(node), config=config)
    expected_struct = Dictionary({
        'x': Unknown(label='x', linenos=[1]),
        'y': Scalar(label='y', linenos=[1]),
    })
    assert struct == expected_struct

    template = '''{{ x|customfilter(y, z) }}'''
    node = parse(template).find(nodes.Filter)
    rtype, struct = visit_filter(node, get_scalar_context(node), config=config)
    expected_struct = Dictionary({
        'x': Unknown(label='x', linenos=[1]),
        'y': Scalar(label='y', linenos=[1]),
        'z': Scalar(label='z', linenos=[1]),
    })
    assert struct == expected_struct

def test_custom_filter_arguments():
    def dummy_filter(value1, value2):
      return value2
    filters = [
      {
        'customfilter': dummy_filter
      }
    ]
    config = Config(CUSTOM_FILTERS=filters, RAISE_ON_NO_FILTER=True, RAISE_ON_INVALID_FILTER_ARGS=True)
    template = '''{{ x|customfilter }}'''
    node = parse(template).find(nodes.Filter)
    with pytest.raises(InvalidExpression) as e:
        visit_filter(node, get_scalar_context(node), config=config)
    assert 'amount of params' in str(e.value)

    template = '''{{ x|customfilter(y) }}'''
    node = parse(template).find(nodes.Filter)
    rtype, struct = visit_filter(node, get_scalar_context(node), config=config)
    expected_struct = Dictionary({
        'x': Unknown(label='x', linenos=[1]),
        'y': Scalar(label='y', linenos=[1]),
    })
    assert struct == expected_struct

    template = '''{{ x|customfilter(y, z) }}'''
    node = parse(template).find(nodes.Filter)
    with pytest.raises(InvalidExpression) as e:
        visit_filter(node, get_scalar_context(node), config=config)
    assert 'amount of params' in str(e.value)

def test_custom_filter_arguments_self():
    def dummy_filter(self, value1, value2):
      return value2
    filters = [
      {
        'customfilter': dummy_filter
      }
    ]
    config = Config(CUSTOM_FILTERS=filters, RAISE_ON_NO_FILTER=True, RAISE_ON_INVALID_FILTER_ARGS=True)
    template = '''{{ x|customfilter }}'''
    node = parse(template).find(nodes.Filter)
    with pytest.raises(InvalidExpression) as e:
        visit_filter(node, get_scalar_context(node), config=config)
    assert 'amount of params' in str(e.value)

    template = '''{{ x|customfilter(y) }}'''
    node = parse(template).find(nodes.Filter)
    rtype, struct = visit_filter(node, get_scalar_context(node), config=config)
    expected_struct = Dictionary({
        'x': Unknown(label='x', linenos=[1]),
        'y': Scalar(label='y', linenos=[1]),
    })
    assert struct == expected_struct

    template = '''{{ x|customfilter(y, z) }}'''
    node = parse(template).find(nodes.Filter)
    with pytest.raises(InvalidExpression) as e:
        visit_filter(node, get_scalar_context(node), config=config)
    assert 'amount of params' in str(e.value)

def test_custom_filter_self_class():
    class DummyFilters(object):
      def dummy_filter(self, value1, value2):
        return value2
      def filters(self):
        return {
            'customfilter': self.dummy_filter
        }
    config = Config(CUSTOM_FILTERS=[DummyFilters()], RAISE_ON_NO_FILTER=True, RAISE_ON_INVALID_FILTER_ARGS=True)
    template = '''{{ x|customfilter }}'''
    node = parse(template).find(nodes.Filter)
    with pytest.raises(InvalidExpression) as e:
        visit_filter(node, get_scalar_context(node), config=config)
    assert 'amount of params' in str(e.value)

    template = '''{{ x|customfilter(y) }}'''
    node = parse(template).find(nodes.Filter)
    rtype, struct = visit_filter(node, get_scalar_context(node), config=config)
    expected_struct = Dictionary({
        'x': Unknown(label='x', linenos=[1]),
        'y': Scalar(label='y', linenos=[1]),
    })
    assert struct == expected_struct

    template = '''{{ x|customfilter(y, z) }}'''
    node = parse(template).find(nodes.Filter)
    with pytest.raises(InvalidExpression) as e:
        visit_filter(node, get_scalar_context(node), config=config)
    assert 'amount of params' in str(e.value)











def test_custom_filter_arguments():
    def dummy_filter(value1, value2='test'):
      return value2
    filters = [
      {
        'customfilter': dummy_filter
      }
    ]
    config = Config(CUSTOM_FILTERS=filters, RAISE_ON_NO_FILTER=True, RAISE_ON_INVALID_FILTER_ARGS=True)
    template = '''{{ x|customfilter }}'''
    node = parse(template).find(nodes.Filter)
    rtype, struct = visit_filter(node, get_scalar_context(node), config=config)
    expected_struct = Dictionary({
        'x': Unknown(label='x', linenos=[1])
    })
    assert struct == expected_struct

    template = '''{{ x|customfilter(y) }}'''
    node = parse(template).find(nodes.Filter)
    rtype, struct = visit_filter(node, get_scalar_context(node), config=config)
    expected_struct = Dictionary({
        'x': Unknown(label='x', linenos=[1]),
        'y': Scalar(label='y', linenos=[1]),
    })
    assert struct == expected_struct

    template = '''{{ x|customfilter(y, z) }}'''
    node = parse(template).find(nodes.Filter)
    with pytest.raises(InvalidExpression) as e:
        visit_filter(node, get_scalar_context(node), config=config)
    assert 'amount of params' in str(e.value)

def test_custom_filter_arguments_self():
    def dummy_filter(self, value1, value2='test'):
      return value2
    filters = [
      {
        'customfilter': dummy_filter
      }
    ]
    config = Config(CUSTOM_FILTERS=filters, RAISE_ON_NO_FILTER=True, RAISE_ON_INVALID_FILTER_ARGS=True)
    template = '''{{ x|customfilter }}'''
    node = parse(template).find(nodes.Filter)
    rtype, struct = visit_filter(node, get_scalar_context(node), config=config)
    expected_struct = Dictionary({
        'x': Unknown(label='x', linenos=[1])
    })
    assert struct == expected_struct

    template = '''{{ x|customfilter(y) }}'''
    node = parse(template).find(nodes.Filter)
    rtype, struct = visit_filter(node, get_scalar_context(node), config=config)
    expected_struct = Dictionary({
        'x': Unknown(label='x', linenos=[1]),
        'y': Scalar(label='y', linenos=[1]),
    })
    assert struct == expected_struct

    template = '''{{ x|customfilter(y, z) }}'''
    node = parse(template).find(nodes.Filter)
    with pytest.raises(InvalidExpression) as e:
        visit_filter(node, get_scalar_context(node), config=config)
    assert 'amount of params' in str(e.value)

def test_custom_filter_self_class():
    class DummyFilters2(object):
      def dummy_filter(self, value1, value2='test'):
        return value2
      def filters(self):
        return {
            'customfilter': self.dummy_filter
        }
    config = Config(CUSTOM_FILTERS=[DummyFilters2()], RAISE_ON_NO_FILTER=True, RAISE_ON_INVALID_FILTER_ARGS=True)
    template = '''{{ x|customfilter }}'''
    node = parse(template).find(nodes.Filter)
    rtype, struct = visit_filter(node, get_scalar_context(node), config=config)
    expected_struct = Dictionary({
        'x': Unknown(label='x', linenos=[1])
    })
    assert struct == expected_struct

    template = '''{{ x|customfilter(y) }}'''
    node = parse(template).find(nodes.Filter)
    rtype, struct = visit_filter(node, get_scalar_context(node), config=config)
    expected_struct = Dictionary({
        'x': Unknown(label='x', linenos=[1]),
        'y': Scalar(label='y', linenos=[1]),
    })
    assert struct == expected_struct

    template = '''{{ x|customfilter(y, z) }}'''
    node = parse(template).find(nodes.Filter)
    with pytest.raises(InvalidExpression) as e:
        visit_filter(node, get_scalar_context(node), config=config)
    assert 'amount of params' in str(e.value)















def test_raise_on_unknown_filter():
    def dummy_filter(self, value1, value2):
      return value2
    filters = [
      {
        'customfilter': dummy_filter
      }
    ]
    config = Config(CUSTOM_FILTERS=filters, RAISE_ON_NO_FILTER=True)
    template = '''{{ x|unknownfilter }}'''
    node = parse(template).find(nodes.Filter)
    config = Config(RAISE_ON_NO_FILTER=True)
    with pytest.raises(InvalidExpression) as e:
        visit_filter(node, get_scalar_context(node), config=config)
    assert 'unknown filter' in str(e.value)

    template = '''{{ x|attr('attr') }}'''
    node = parse(template).find(nodes.Filter)
    with pytest.raises(InvalidExpression) as e:
        visit_filter(node, get_scalar_context(node))
    assert 'filter is not supported' in str(e.value)

def test_raise_on_unknown_filter():
    template = '''{{ x|unknownfilter }}'''
    node = parse(template).find(nodes.Filter)
    config = Config(RAISE_ON_NO_FILTER=True)
    with pytest.raises(InvalidExpression) as e:
        visit_filter(node, get_scalar_context(node), config=config)
    assert 'unknown filter' in str(e.value)

    template = '''{{ x|attr('attr') }}'''
    node = parse(template).find(nodes.Filter)
    with pytest.raises(InvalidExpression) as e:
        visit_filter(node, get_scalar_context(node))
    assert 'filter is not supported' in str(e.value)


def test_abs_filter():
    node = parse('{{ x|abs }}').find(nodes.Filter)
    rtype, struct = visit_filter(node, get_scalar_context(node))
    assert rtype == Number(label='x', linenos=[1])
    assert struct == Dictionary({
        'x': Number(label='x', linenos=[1])
    })


def test_int_filter():
    node = parse('{{ x|int }}').find(nodes.Filter)
    rtype, struct = visit_filter(node, get_scalar_context(node))
    assert rtype == Number(label='x', linenos=[1])
    assert struct == Dictionary({
        'x': Scalar(label='x', linenos=[1]),
    })


def test_wordcount_filter():
    node = parse('{{ x|wordcount }}').find(nodes.Filter)
    rtype, struct = visit_filter(node, get_scalar_context(node))
    assert rtype == Number(label='x', linenos=[1])
    assert struct == Dictionary({
        'x': String(label='x', linenos=[1])
    })


def test_join_filter():
    node = parse('{{ xs|join(separator|default("|")) }}').find(nodes.Filter)
    rtype, struct = visit_filter(node, get_scalar_context(node))
    assert rtype == String(label='xs', linenos=[1])
    assert struct == Dictionary({
        'xs': List(String(), label='xs', linenos=[1]),
        'separator': String(label='separator', linenos=[1], used_with_default=True, value='|'),
    })


def test_length_filter():
    node = parse('{{ xs|length }}').find(nodes.Filter)
    rtype, struct = visit_filter(node, get_scalar_context(node))
    assert rtype == Number(label='xs', linenos=[1])
    assert struct == Dictionary({
        'xs': List(Unknown(), label='xs', linenos=[1]),
    })