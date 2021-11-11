# coding: utf-8
"""
jinja2schema.visitors.stmt
~~~~~~~~~~~~~~~~~~~~~~~~~~

Statement is an instance of :class:`jinja2.nodes.Stmt`.
Statement visitors return :class:`.models.Dictionary` of structures of variables used within the statement.
"""
import functools

from jinja2 import nodes, Environment, PackageLoader
from jinja2schema.config import default_config

from ..model import Scalar, Dictionary, List, Variable, Tuple
from ..macro import Macro
from ..mergers import merge, merge_many
from ..exceptions import InvalidExpression
from .._compat import iteritems, izip, zip_longest
from .expr import Context, visit_expr
from .util import visit_many


stmt_visitors = {}


def visits_stmt(node_cls):
    """Decorator that registers a function as a visitor for ``node_cls``.

    :param node_cls: subclass of :class:`jinja2.nodes.Stmt`
    """
    def decorator(func):
        stmt_visitors[node_cls] = func
        @functools.wraps(func)
        def wrapped_func(node, macroses=None, config=default_config, child_blocks=None):
            assert isinstance(node, node_cls)
            return func(node, macroses, config, child_blocks)
        return wrapped_func
    return decorator


def visit_stmt(node, macroses=None, config=default_config, child_blocks=None):
    """Returns a structure of ``node``.

    :param node: instance of :class:`jinja2.nodes.Stmt`
    :returns: :class:`.model.Dictionary`
    """
    visitor = stmt_visitors.get(type(node))
    if not visitor:
        for node_cls, visitor_ in iteritems(stmt_visitors):
            if isinstance(node, node_cls):
                visitor = visitor_
    if not visitor:
        raise Exception('stmt visitor for {0} is not found'.format(type(node)))
    return visitor(node, macroses, config)


@visits_stmt(nodes.For)
def visit_for(node, macroses=None, config=default_config, child_blocks=None):
    body_struct = visit_many(node.body, macroses, config, predicted_struct_cls=Scalar)
    else_struct = visit_many(node.else_, macroses, config, predicted_struct_cls=Scalar)

    if 'loop' in body_struct:
        # exclude a special `loop` variable from the body structure
        del body_struct['loop']

    if isinstance(node.target, nodes.Tuple):
        target_struct = Tuple.from_node(
            node.target,
            [body_struct.pop(item.name, Variable.from_node(node.target))
            for item in node.target.items])
    else:
        target_struct = Variable.from_node(node.target)
        # target_struct = body_struct.pop(node.target.name, Variable.from_node(node))

    iter_rtype, iter_struct = visit_expr(
        node.iter,
        Context(
            return_struct_cls=Variable,
            predicted_struct=List.from_node(node, target_struct)),
        macroses, config)

    merge(iter_rtype, List(target_struct))

    return merge_many(iter_struct, body_struct, else_struct)


@visits_stmt(nodes.If)
def visit_if(node, macroses=None, config=default_config, child_blocks=None):
    if config.BOOLEAN_CONDITIONS:
        test_predicted_struct = Scalar.from_node(node.test)
    else:
        test_predicted_struct = Variable.from_node(node.test)
    test_rtype, test_struct = visit_expr(
            node.test, Context(predicted_struct=test_predicted_struct), macroses, config)
    if_struct = visit_many(node.body, macroses, config, predicted_struct_cls=Scalar)
    else_struct = visit_many(node.else_, macroses, config, predicted_struct_cls=Scalar) if node.else_ else Dictionary()
    struct = merge_many(test_struct, if_struct, else_struct)

    for var_name, var_struct in iteritems(test_struct):
        if var_struct.checked_as_defined or var_struct.checked_as_undefined:
            if var_struct.checked_as_undefined:
                lookup_struct = if_struct
            elif var_struct.checked_as_defined:
                lookup_struct = else_struct
            struct[var_name].may_be_defined = (lookup_struct and
                                               var_name in lookup_struct and
                                               lookup_struct[var_name].constant)
            struct[var_name].checked_as_defined = test_struct[var_name].checked_as_defined and (
                not lookup_struct or not var_name in lookup_struct or lookup_struct[var_name].constant
            )
            struct[var_name].checked_as_undefined = test_struct[var_name].checked_as_undefined and (
                not lookup_struct or not var_name in lookup_struct or lookup_struct[var_name].constant
            )
    return struct


@visits_stmt(nodes.Assign)
def visit_assign(node, macroses=None, config=default_config, child_blocks=None):
    struct = Dictionary()
    if (isinstance(node.target, nodes.Name) or
            (isinstance(node.target, nodes.Tuple) and isinstance(node.node, nodes.Tuple))):
        variables = []
        if not (isinstance(node.target, nodes.Tuple) and isinstance(node.node, nodes.Tuple)):
            variables.append((node.target.name, node.node))
        else:
            if len(node.target.items) != len(node.node.items):
                raise InvalidExpression(node, 'number of items in left side is different '
                                             'from right side')
            for name_node, var_node in izip(node.target.items, node.node.items):
                variables.append((name_node.name, var_node))
        for var_name, var_node in variables:
            var_rtype, var_struct = visit_expr(var_node, Context(
                predicted_struct=Variable.from_node(var_node)), macroses, config)
            var_rtype.constant = True
            var_rtype.label = var_name
            struct = merge_many(struct, var_struct, Dictionary({
                var_name: var_rtype,
            }))
        return struct
    elif isinstance(node.target, nodes.Tuple):
        tuple_items = []
        for name_node in node.target.items:
            var_struct = Variable.from_node(name_node, constant=True)
            tuple_items.append(var_struct)
            struct = merge(struct, Dictionary({name_node.name: var_struct}))
        var_rtype, var_struct = visit_expr(
            node.node, Context(return_struct_cls=Variable, predicted_struct=Tuple(tuple_items)), macroses, config)
        return merge(struct, var_struct)
    else:
        raise InvalidExpression(node, 'unsupported assignment')


@visits_stmt(nodes.Output)
def visit_output(node, macroses=None, config=default_config, child_blocks=None):
    return visit_many(node.nodes, macroses, config, predicted_struct_cls=Scalar)


@visits_stmt(nodes.Macro)
def visit_macro(node, macroses=None, config=default_config, child_blocks=None):
    # XXX the code needs to be refactored
    args = []
    kwargs = []
    body_struct = visit_many(node.body, macroses, config, predicted_struct_cls=Scalar)

    for i, (arg, default_value_node) in enumerate(reversed(list(zip_longest(reversed(node.args),
                                                                           reversed(node.defaults)))), start=1):
        has_default_value = bool(default_value_node)
        if has_default_value:
            default_rtype, default_struct = visit_expr(
                default_value_node, Context(predicted_struct=Variable()), macroses, config)
        else:
            default_rtype = Variable(linenos=[arg.lineno])
        default_rtype.constant = False
        default_rtype.label = 'argument "{0}"'.format(arg.name) if has_default_value else 'argument #{0}'.format(i)
        if arg.name in body_struct:
            default_rtype = merge(default_rtype, body_struct[arg.name])  # just to make sure
        default_rtype.linenos = [node.lineno]
        if has_default_value:
            kwargs.append((arg.name, default_rtype))
        else:
            args.append((arg.name, default_rtype))
    macroses[node.name] = Macro(node.name, args, kwargs)

    tmp = dict(args)
    tmp.update(dict(kwargs))
    args_struct = Dictionary(tmp)
    for arg_name, arg_type in args:
        args_struct[arg_name] = arg_type

    for arg in args_struct.iterkeys():
        body_struct.pop(arg, None)
    return body_struct


@visits_stmt(nodes.Block)
def visit_block(node, macroses=None, config=default_config):
    return visit_many(node.body, macroses, config)


@visits_stmt(nodes.Include)
def visit_include(node, macroses=None, config=default_config, child_blocks=None):
    template = get_inherited_template(config, node)
    return visit_many(template.body, macroses, config)


@visits_stmt(nodes.Extends)
def visit_extends(node, macroses=None, config=default_config, child_blocks=None):
    template = get_inherited_template(config, node)
    if not child_blocks:
        return visit_many(template.body, macroses, config)
    return visit_many(get_correct_nodes(child_blocks, template.body), None, config)


def get_inherited_template(config, node):
    env = Environment(loader=PackageLoader(config.PACKAGE_NAME, config.TEMPLATE_DIR))
    return env.parse(env.loader.get_source(env, node.template.value)[0])


def separate_template_blocks(template, blocks, template_nodes):
    for node in template:
        if isinstance(node, nodes.Block):
            blocks.append(node)
        else:
            template_nodes.append(node)
    return blocks, template_nodes


def get_correct_nodes(child_blocks, template):
    parent_blocks, nodes = separate_template_blocks(template, [], [])
    child_block_names = [c.name for c in child_blocks]
    blocks = child_blocks + parent_blocks
    for parent_block in parent_blocks:
        if parent_block.name in child_block_names:
            blocks.remove(parent_block)
    return blocks + nodes
