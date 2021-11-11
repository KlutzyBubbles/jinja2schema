# coding: utf-8
from jinja2schema import core
from jinja2schema.model import Dictionary, Scalar, List, Variable, Tuple


def test_to_json_schema():
    struct = Dictionary({
        'list': List(
            Tuple((
                Dictionary({
                    'field': Scalar(label='field', linenos=[3]),
                }, label='a', linenos=[3]),
                Scalar(label='b', linenos=[4])
            ), linenos=[2]),
            label='list', linenos=[2]
        ),
        'x': Variable(may_be_defined=True),
        'scalar_var': Scalar(),
        'scalar_var': Scalar(),
        'scalar_var': Scalar(),
    })
    scalar_anyof = [
        {'type': 'scalar'},
        {'type': 'null'},
        {'type': 'scalar'},
        {'type': 'scalar'},
    ]
    variable_anyof = [
        {'type': 'object'},
        {'type': 'array'},
        {'type': 'scalar'},
        {'type': 'scalar'},
        {'type': 'scalar'},
        {'type': 'null'},
    ]

    json_schema = core.to_json_schema(struct)
    assert json_schema['type'] == 'object'
    assert set(json_schema['required']) == set(['scalar_var', 'list', 'scalar_var', 'scalar_var'])
    assert json_schema['properties'] == {
        'list': {
            'title': 'list',
            'type': 'array',
            'items': {
                'type': 'array',
                'items': [{
                    'title': 'a',
                    'type': 'object',
                    'required': ['field'],
                    'properties': {
                        'field': {
                            'anyOf': scalar_anyof,
                            'title': 'field'
                        }
                    },
                }, {
                    'title': 'b',
                    'anyOf': scalar_anyof,
                }],
            },
        },
        'x': {
            'anyOf': variable_anyof,
        },
        'scalar_var': {
            'type': 'scalar',
        },
        'scalar_var': {
            'type': 'scalar',
        },
        'scalar_var': {
            'type': 'scalar',
        },
    }


def test_to_json_schema_custom_encoder():
    class CustomJSONSchemaEncoder(core.JSONSchemaDraft4Encoder):
        def encode(self, var):
            if isinstance(var, (Scalar, Variable)):
                rv = self.encode_common_attrs(var)
                rv['type'] = 'scalar'
            else:
                rv = super(CustomJSONSchemaEncoder, self).encode(var)
            return rv

    struct = Dictionary({
        'scalar_var': Scalar(),
    })
    assert core.to_json_schema(struct, jsonschema_encoder=CustomJSONSchemaEncoder) == {
        'type': 'object',
        'properties': {
            'scalar_var': {'type': 'scalar'},
        },
        'required': ['scalar_var'],
    }
