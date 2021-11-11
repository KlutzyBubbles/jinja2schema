import functools
from inspect import getargspec, ismethod
from jinja2 import nodes

from ..model import Scalar, Dictionary, List, Tuple, Variable
from ..mergers import merge_rtypes, merge, merge_many, merge_bool_expr_structs
from ..exceptions import InvalidExpression, UnexpectedExpression, MergeException
from ..config import default_config
from .. import _compat
from .util import visit_many


class Context(object):
    """
    Context is used when parsing expressions.

    Suppose there is an expression::

        {{ data.field.subfield }}

    It has the following NODE::

        Getattr(
            node=Getattr(
                node=Name(name='data')
                attr='field'
            ),
            attr='subfield'
        )

    :func:`visit_getattr` returns a pair that looks like this::

        (
            # return type:
            Scalar(...),
            # structure:
            {
                'data: {
                    'field': {
                        'subfield': Scalar(...)
                    }
                }
            }
        }

    The return type is defined by the outermost :class:`nodes.Getattr` node, which
    in this case is being printed.
    The structure is build during NODE traversal from outer to inners nodes and it is
    kind of "reversed" in relation to the NODE.
    :class:`Context` is intended for:

    * capturing a return type and passing it to the innermost expression node;
    * passing a structure "under construction" to the visitors of nested nodes.

    Let's look through an example.

    Suppose :func:`visit_getattr` is called with the following arguments::

       node = Getattr(node=Getattr(node=Name(name='data'), attr='field'), attr='subfield'))
       context = Context(return_struct_cls=Scalar, predicted_struct=Scalar())

    It looks to the outermost NODE node and based on it's type (which is :class:`nodes.Getattr`)
    and it's ``attr`` field (which equals to ``"subfield"``) infers that a variable described by the
    nested NODE node must a dictionary with ``"subfield"`` key.

    It calls a visitor for inner node and :func:`visit_getattr` gets called again, but
    with different arguments::

       node = Getattr(node=Name(name='data', ctx='load'), attr='field')
       ctx = Context(return_struct_cls=Scalar, predicted_struct=Dictionary({subfield: Scalar()}))

    :func:`visit_getattr` applies the same logic again. The inner node is a :class:`nodes.Name`, so that
    it calls :func:`visit_name` with the following arguments::

       node = Name(name='data')
       ctx = Context(
           return_struct_cls=Scalar,
           predicted_struct=Dictionary({
               field: Dictionary({subfield: Scalar()}))
           })
       )

    :func:`visit_name` does not do much by itself. Based on a context it knows what structure and
    what type must have a variable described by a given :class:`nodes.Name` node, so
    it just returns a pair::

        (instance of context.return_struct_cls, Dictionary({data: context.predicted_struct}})
    """
    def __init__(self, ctx=None, return_struct_cls=None, predicted_struct=None):
        self.predicted_struct = None
        self.return_struct_cls = Variable
        if ctx:
            self.predicted_struct = ctx.predicted_struct
            self.return_struct_cls = ctx.return_struct_cls
        if predicted_struct:
            self.predicted_struct = predicted_struct
        if return_struct_cls:
            self.return_struct_cls = return_struct_cls

    def get_predicted_struct(self, label=None):
        rv = self.predicted_struct.clone()
        if label:
            rv.label = label
        return rv

    def meet(self, actual_struct, actual_node):
        try:
            merge(self.predicted_struct, actual_struct)
        except MergeException:
            raise UnexpectedExpression(
                self.predicted_struct, actual_node, actual_struct)
        else:
            return True


expr_visitors = {}


def visits_expr(node_cls):
    """Decorator that registers a function as a visitor for ``node_cls``.

    :param node_cls: subclass of :class:`jinja2.nodes.Expr`
    """
    def decorator(func):
        expr_visitors[node_cls] = func
        @functools.wraps(func)
        def wrapped_func(node, ctx, macroses=None, config=default_config):
            assert isinstance(node, node_cls)
            return func(node, ctx, macroses=macroses, config=config)
        return wrapped_func
    return decorator


def visit_expr(node, ctx, macroses=None, config=default_config):
    """Returns a structure of ``node``.

    :param ctx: :class:`Context`
    :param node: instance of :class:`jinja2.nodes.Expr`
    :returns: a tuple where the first element is an expression type (instance of :class:`Variable`)
              and the second element is an expression structure (instance of :class:`.model.Dictionary`)
    """
    visitor = expr_visitors.get(type(node))
    if not visitor:
        for node_cls, visitor_ in _compat.iteritems(expr_visitors):
            if isinstance(node, node_cls):
                visitor = visitor_
    if not visitor:
        raise Exception(
            'expression visitor for {0} is not found'.format(type(node)))
    return visitor(node, ctx, macroses, config=config)


def _visit_dict(node, ctx, macroses, items, config=default_config):
    """A common logic behind nodes.Dict and nodes.Call (``{{ dict(a=1) }}``)
    visitors.

    :param items: a list of (key, value); key may be either NODE node or string
    """
    ctx.meet(Dictionary(), node)
    rtype = Dictionary.from_node(
        node, constant=True)
    struct = Dictionary()
    for key, value in items:
        value_rtype, value_struct = visit_expr(value, Context(
            predicted_struct=Variable.from_node(value)), macroses, config=config)
        struct = merge(struct, value_struct)
        if isinstance(key, nodes.Node):
            key_rtype, key_struct = visit_expr(key, Context(
                predicted_struct=Scalar.from_node(key)), macroses,
                config=config)
            struct = merge(struct, key_struct)
            if isinstance(key, nodes.Const):
                rtype[key.value] = value_rtype
        elif isinstance(key, _compat.string_types):
            rtype[key] = value_rtype
    return rtype, struct


@visits_expr(nodes.BinExpr)
def visit_bin_expr(node, ctx, macroses=None, config=default_config):
    l_rtype, l_struct = visit_expr(node.left, ctx, macroses, config=config)
    r_rtype, r_struct = visit_expr(node.right, ctx, macroses, config=config)
    rv = merge_bool_expr_structs(l_struct, r_struct)
    return merge_rtypes(l_rtype, r_rtype, operator=node.operator), rv


@visits_expr(nodes.UnaryExpr)
def visit_unary_expr(node, ctx, macroses=None, config=default_config):
    return visit_expr(node.node, ctx, macroses, config=config)


@visits_expr(nodes.Compare)
def visit_compare(node, ctx, macroses=None, config=default_config):
    ctx.meet(Scalar(), node)
    rtype, struct = visit_expr(node.expr, Context(
        predicted_struct=Variable.from_node(node.expr)), macroses, config=config)
    for op in node.ops:
        op_rtype, op_struct = visit_expr(op.expr, Context(
            predicted_struct=Variable.from_node(node.expr)), macroses,
            config=config)
        struct = merge(struct, op_struct)
    return Scalar.from_node(node), struct


@visits_expr(nodes.Slice)
def visit_slice(node, ctx, macroses=None, config=default_config):
    nodes = [node for node in [node.start,
                               node.stop, node.step] if node is not None]
    struct = visit_many(nodes, macroses, config,
                        predicted_struct_cls=Scalar,
                        return_struct_cls=Scalar)
    return Variable(), struct


@visits_expr(nodes.Name)
def visit_name(node, ctx, macroses=None, config=default_config):
    return ctx.return_struct_cls.from_node(node), Dictionary({
        node.name: ctx.get_predicted_struct(label=node.name)
    })


@visits_expr(nodes.Getattr)
def visit_getattr(node, ctx, macroses=None, config=default_config):
    ctx = Context(
        ctx=ctx,
        predicted_struct=Dictionary.from_node(node, {
            node.attr: ctx.get_predicted_struct(label=node.attr),
        }))
    test1, test2 = visit_expr(node.node, ctx, macroses, config=config)
    return test1, test2


@visits_expr(nodes.Getitem)
def visit_getitem(node, ctx, macroses=None, config=default_config):
    arg = node.arg
    if isinstance(arg, nodes.Const):
        if isinstance(arg.value, int):
            predicted_struct = Variable.from_node(node)
            # if config.TYPE_OF_VARIABLE_INDEXED_WITH_INTEGER_TYPE == 'list':
            #     predicted_struct = List.from_node(node, ctx.get_predicted_struct())
            # elif config.TYPE_OF_VARIABLE_INDEXED_WITH_INTEGER_TYPE == 'dictionary':
            #     predicted_struct = Dictionary.from_node(node, {
            #         arg.value: ctx.get_predicted_struct(),
            #     })
            # elif config.TYPE_OF_VARIABLE_INDEXED_WITH_INTEGER_TYPE == 'tuple':
            #     items = [Variable() for i in range(arg.value + 1)]
            #     items[arg.value] = ctx.get_predicted_struct()
            #     predicted_struct = Tuple.from_node(node, tuple(items), may_be_extended=True)
        elif isinstance(arg.value, _compat.string_types):
            predicted_struct = Dictionary.from_node(node, {
                arg.value: ctx.get_predicted_struct(label=arg.value),
            })
        else:
            raise InvalidExpression(arg, '{0} is not supported as an index for a list or'
                                         ' a key for a dictionary'.format(arg.value))
    elif isinstance(arg, nodes.Slice):
        predicted_struct = List.from_node(
            node, ctx.get_predicted_struct())
    else:
      predicted_struct = Variable.from_node(node)
        # if config.TYPE_OF_VARIABLE_INDEXED_WITH_VARIABLE_TYPE == 'list':
        #     predicted_struct = List.from_node(
        #         node, ctx.get_predicted_struct())
        # elif config.TYPE_OF_VARIABLE_INDEXED_WITH_VARIABLE_TYPE == 'dictionary':
        #     predicted_struct = Dictionary.from_node(
        #         node)

    _, arg_struct = visit_expr(arg,
                               Context(predicted_struct=Scalar.from_node(
                                   arg)),
                               macroses, config=config)
    rtype, struct = visit_expr(node.node, Context(
        ctx=ctx,
        predicted_struct=predicted_struct), macroses, config=config)
    return rtype, merge(struct, arg_struct)


@visits_expr(nodes.Test)
def visit_test(node, ctx, macroses=None, config=default_config):
    ctx.meet(Scalar(), node)
    if node.name in ('divisibleby', 'escaped', 'even', 'lower', 'odd', 'upper'):
        # TODO
        predicted_struct = Scalar.from_node(
            node.node)
    elif node.name in ('defined', 'undefined', 'equalto', 'iterable', 'mapping',
                      'none', 'number', 'sameas', 'sequence', 'string'):
        predicted_struct = Variable.from_node(
            node.node)
        if node.name == 'defined':
            predicted_struct.checked_as_defined = True
        elif node.name == 'undefined':
            predicted_struct.checked_as_undefined = True
    else:
        raise InvalidExpression(node, 'unknown test "{0}"'.format(node.name))
    rtype, struct = visit_expr(node.node, Context(return_struct_cls=Scalar,
                                                 predicted_struct=predicted_struct), macroses, config=config)
    if node.name == 'divisibleby':
        if not node.args:
            raise InvalidExpression(node, 'divisibleby must have an argument')
        _, arg_struct = visit_expr(node.args[0],
                                   Context(predicted_struct=Scalar.from_node(node.args[0])),
                                   macroses, config=config)
        struct = merge(arg_struct, struct)
    return rtype, struct


@visits_expr(nodes.Concat)
def visit_concat(node, ctx, macroses=None, config=default_config):
    ctx.meet(Scalar(), node)
    return Scalar.from_node(node), visit_many(node.nodes, macroses, config,
                                                                                     predicted_struct_cls=Scalar)


@visits_expr(nodes.CondExpr)
def visit_cond_expr(node, ctx, macroses=None, config=default_config):
    if config.BOOLEAN_CONDITIONS:
        test_predicted_struct = Scalar.from_node(
            node.test)
    else:
        test_predicted_struct = Variable.from_node(
            node.test)
    test_rtype, test_struct = visit_expr(node.test, Context(predicted_struct=test_predicted_struct), macroses,
                                         config=config)
    if_rtype, if_struct = visit_expr(node.expr1, ctx, macroses, config=config)
    else_rtype, else_struct = visit_expr(
        node.expr2, ctx, macroses, config=config)
    struct = merge_many(if_struct, test_struct, else_struct)
    rtype = merge_rtypes(if_rtype, else_rtype)

    for var_name, var_struct in test_struct.iteritems():
        if var_struct.checked_as_defined or var_struct.checked_as_undefined:
            if var_struct.checked_as_undefined:
                lookup_struct = if_struct
            elif var_struct.checked_as_defined:
                lookup_struct = else_struct
            struct[var_name].may_be_defined = (lookup_struct and
                                               var_name in lookup_struct and
                                               lookup_struct[var_name].constant)
            struct[var_name].checked_as_defined = test_struct[var_name].checked_as_defined and (
                not lookup_struct or not var_name in lookup_struct or lookup_struct[
                    var_name].constant
            )
            struct[var_name].checked_as_undefined = test_struct[var_name].checked_as_undefined and (
                not lookup_struct or not var_name in lookup_struct or lookup_struct[
                    var_name].constant
            )

    return rtype, struct


@visits_expr(nodes.Call)
def visit_call(node, ctx, macroses=None, config=default_config):
    if isinstance(node.node, nodes.Name):
        if macroses and node.node.name in macroses:
            macro = macroses[node.node.name]
            call = MacroCall(macro, node.args, node.kwargs, config=config)
            args_struct = call.match_passed_args_to_expected_args()
            if call.passed_args:
                args_struct = merge(
                    args_struct, call.match_passed_args_to_expected_kwargs())
            if call.passed_kwargs:
                args_struct = merge(
                    args_struct, call.match_passed_kwargs_to_expected_args())
            if call.passed_kwargs:
                args_struct = merge(
                    args_struct, call.match_passed_kwargs_to_expected_kwargs())

            if call.passed_args or call.expected_args:
                raise InvalidExpression(node, ('incorrect usage of "{0}". it takes '
                                              'exactly {1} positional arguments'.format(macro.name, len(macro.args))))
            if call.passed_kwargs:
                first_unknown_kwarg = next(
                    _compat.iterkeys(call.passed_kwargs))
                raise InvalidExpression(node, ('incorrect usage of "{0}". unknown keyword argument '
                                              '"{1}" is passed'.format(macro.name, first_unknown_kwarg)))
            return Variable(), args_struct
        elif node.node.name == 'range':
            ctx.meet(List(Variable()), node)
            struct = Dictionary()
            for arg in node.args:
                arg_rtype, arg_struct = visit_expr(arg, Context(
                    predicted_struct=Scalar.from_node(arg)), macroses,
                    config=config)
                struct = merge(struct, arg_struct)
            return List(Scalar()), struct
        elif node.node.name == 'lipsum':
            ctx.meet(Scalar(), node)
            struct = Dictionary()
            # probable TODO: set possible types for args and kwargs
            for arg in node.args:
                arg_rtype, arg_struct = visit_expr(arg, Context(
                    predicted_struct=Scalar.from_node(arg)), macroses,
                    config=config)
                struct = merge(struct, arg_struct)
            for kwarg in node.kwargs:
                arg_rtype, arg_struct = visit_expr(kwarg.value, Context(
                    predicted_struct=Scalar.from_node(kwarg)), macroses,
                    config=config)
                struct = merge(struct, arg_struct)
            return Scalar(), struct
        elif node.node.name == 'dict':
            ctx.meet(Dictionary(), node)
            if node.args:
                raise InvalidExpression(
                    node, 'dict accepts only keyword arguments')
            return _visit_dict(node, ctx, macroses, [(kwarg.key, kwarg.value) for kwarg in node.kwargs], config=config)
        else:
            raise InvalidExpression(
                node, '"{0}" call is not supported'.format(node.node.name))
    elif isinstance(node.node, nodes.Getattr):
        if node.node.attr in ('keys', 'iterkeys', 'values', 'itervalues'):
            ctx.meet(List(Variable()), node)
            rtype, struct = visit_expr(
                node.node.node, Context(
                    predicted_struct=Dictionary.from_node(node.node.node)),
                macroses, config=config)
            return List(Variable()), struct
        if node.node.attr in ('startswith', 'endswith'):
            ctx.meet(Scalar(), node)
            rtype, struct = visit_expr(
                node.node.node,
                Context(predicted_struct=Scalar.from_node(
                    node.node.node)),
                macroses, config=config)
            return Scalar(), struct
        if node.node.attr == 'split':
            ctx.meet(List(Scalar()), node)
            rtype, struct = visit_expr(
                node.node.node,
                Context(predicted_struct=Scalar.from_node(
                    node.node.node)),
                macroses, config=config)
            if node.args:
                arg = node.args[0]
                _, arg_struct = visit_expr(arg, Context(
                    predicted_struct=Scalar.from_node(arg)), macroses,
                    config=config)
                struct = merge(struct, arg_struct)
            return List(Scalar()), struct
        raise InvalidExpression(
            node, '"{0}" call is not supported'.format(node.node.attr))


@visits_expr(nodes.Filter)
def visit_filter(node, ctx, macroses=None, config=default_config):
    return_struct_cls = Variable
    if node.name in ('abs', 'striptags', 'capitalize', 'center', 'escape', 'filesizeformat',
                    'float', 'forceescape', 'format', 'indent', 'int', 'replace', 'round',
                    'safe', 'string', 'striptags', 'title', 'trim', 'truncate', 'upper',
                    'urlencode', 'urlize', 'wordcount', 'wordwrap', 'e'):
        ctx.meet(Scalar(), node)
        if node.name in ('abs', 'round'):
            node_struct = Scalar.from_node(
                node.node)
            return_struct_cls = Scalar
        elif node.name in ('float', 'int'):
            node_struct = Scalar.from_node(
                node.node)
            return_struct_cls = Scalar
        elif node.name in ('striptags', 'capitalize', 'center', 'escape', 'forceescape', 'format', 'indent',
                          'replace', 'safe', 'title', 'trim', 'truncate', 'upper', 'urlencode',
                          'urlize', 'wordwrap', 'e'):
            node_struct = Scalar.from_node(
                node.node)
            return_struct_cls = Scalar
        elif node.name == 'filesizeformat':
            node_struct = Scalar.from_node(
                node.node)
            return_struct_cls = Scalar
        elif node.name == 'string':
            node_struct = Scalar.from_node(
                node.node)
            return_struct_cls = Scalar
        elif node.name == 'wordcount':
            node_struct = Scalar.from_node(
                node.node)
            return_struct_cls = Scalar
        else:
            node_struct = Scalar.from_node(
                node.node)
    elif node.name in ('batch', 'slice'):
        ctx.meet(List(List(Variable())), node)
        rtype = List(List(Variable(), linenos=[node.node.lineno]), linenos=[node.node.lineno])
        node_struct = merge(ctx.get_predicted_struct(), rtype)
        test_, struct = visit_expr(node.node, Context(
            ctx=ctx,
            return_struct_cls=return_struct_cls,
            predicted_struct=node_struct
        ), macroses, config=config)
        return rtype, struct
    elif node.name == 'default':
        predicted_struct = merge(
            Variable(), ctx.get_predicted_struct())
        rtype, struct = visit_expr(node.node, Context(
            return_struct_cls=Variable,
            predicted_struct=predicted_struct
        ), macroses, config=config)
        item_rtype, item_struct = visit_expr(node.args[0], Context(
            predicted_struct=predicted_struct), macroses, config=config)
        struct = merge(struct, item_struct)
        struct.used_with_default = True
        struct.value = item_rtype.value
        return rtype, struct
    elif node.name == 'dictsort':
        ctx.meet(List(Tuple([Scalar(), Variable()])), node)
        node_struct = Dictionary.from_node(
            node.node)
    elif node.name == 'join':
        ctx.meet(Scalar(), node)
        node_struct = List.from_node(
            node.node, Scalar())
        rtype, struct = visit_expr(node.node, Context(
            return_struct_cls=Scalar,
            predicted_struct=node_struct
        ), macroses, config=config)
        arg_rtype, arg_struct = visit_expr(node.args[0],
                                           Context(predicted_struct=Scalar.from_node(node.args[0])),
                                           macroses, config=config)
        return rtype, merge(struct, arg_struct)
    elif node.name in ('first', 'lnode', 'random', 'length', 'sum'):
        if node.name in ('first', 'lnode', 'random'):
            el_struct = ctx.get_predicted_struct()
        elif node.name == 'length':
            ctx.meet(Scalar(), node)
            return_struct_cls = Scalar
            el_struct = Variable()
        else:
            ctx.meet(Scalar(), node)
            el_struct = Scalar()
        node_struct = List.from_node(
            node.node, el_struct)
    elif node.name in ('groupby', 'map', 'reject', 'rejectattr', 'select', 'selectattr', 'sort'):
        ctx.meet(List(Variable()), node)
        node_struct = merge(
            List(Variable()),
            ctx.get_predicted_struct()
        )
    elif node.name == 'list':
        ctx.meet(List(Scalar()), node)
        node_struct = merge(
            List(Scalar.from_node(node.node)),
            ctx.get_predicted_struct()
        ).items
    elif node.name == 'pprint':
        ctx.meet(Scalar(), node)
        node_struct = ctx.get_predicted_struct()
    elif node.name == 'xmlattr':
        ctx.meet(Scalar(), node)
        node_struct = Dictionary.from_node(
            node.node)
    elif node.name == 'attr':
        raise InvalidExpression(node, 'attr filter is not supported')
    else:
        has_filter = False
        for filter_obj in config.CUSTOM_FILTERS:
            if hasattr(filter_obj, 'filters') and ismethod(getattr(filter_obj, 'filters')):
              filters_to_search = filter_obj.filters()
            else:
              filters_to_search = filter_obj
            for name, func in filters_to_search.items():
                if name == node.name:
                    has_filter = True
                    argspec = getargspec(func)
                    args = argspec.args
                    default_args = argspec.args[-len(argspec.defaults):] if argspec.defaults is not None else []
                    if 'self' in args and 'self' not in default_args:
                      args.remove('self')
                    max_arg_count = len(args) - 1
                    min_arg_count = max_arg_count - len(default_args)
                    if argspec.varargs is not None:
                      max_arg_count += 1
                      min_arg_count += 1
                    if argspec.keywords is not None:
                      max_arg_count += 1
                      min_arg_count += 1
                    if max_arg_count < 0 and config.RAISE_ON_INVALID_FILTER_ARGS:
                        raise InvalidExpression(
                            node, 'Filter ' + name + ' needs at lenode 1 argument')
                    if max_arg_count == 0:
                        if node.args is not None and len(node.args) > 0 and config.RAISE_ON_INVALID_FILTER_ARGS:
                            raise InvalidExpression(
                                node, 'Filter ' + name + ' doesn\'t accept parameters')
                        node_struct = Variable.from_node(node.node)
                        return_struct_cls = Variable
                    else:
                        args_provided = 0 if node.args is None else len(node.args)
                        if (args_provided < min_arg_count or args_provided > max_arg_count) and config.RAISE_ON_INVALID_FILTER_ARGS:
                            needs_val = str(min_arg_count)
                            if min_arg_count != max_arg_count:
                              needs_val = str(min_arg_count) + '-' + str(max_arg_count)
                            raise InvalidExpression(node, 'Filter ' + name + ' doesn\'t have the correct amount of params, has: ' + str(
                                len(node.args)) + ', needs: ' + needs_val)
                        node_struct = Variable.from_node(node.node)
                        rtype, struct = visit_expr(node.node, Context(
                            return_struct_cls=Variable,
                            predicted_struct=node_struct
                        ), macroses, config=config)
                        predicted_struct = merge(
                            Variable(), ctx.get_predicted_struct())
                        for arg in node.args:
                            item_rtype, item_struct = visit_expr(arg, Context(
                                predicted_struct=predicted_struct), macroses, config=config)
                            struct = merge(struct, item_struct)
                        for kwarg in node.kwargs:
                            item_rtype, item_struct = visit_expr(kwarg.value, Context(
                                predicted_struct=predicted_struct), macroses, config=config)
                            struct = merge(struct, item_struct)
                        rtype = Variable.from_node(node)
                        return rtype, struct
                    break
        if not has_filter:
            if config.RAISE_ON_NO_FILTER:
                raise InvalidExpression(node, 'unknown filter')
            node_struct = Variable.from_node(node.node)
            rtype, struct = visit_expr(node.node, Context(
                return_struct_cls=Scalar,
                predicted_struct=node_struct
            ), macroses, config=config)
            predicted_struct = merge(Variable(), ctx.get_predicted_struct())
            for arg in node.args:
                item_rtype, item_struct = visit_expr(arg, Context(
                    predicted_struct=predicted_struct), macroses, config=config)
                struct = merge(struct, item_struct)
            rtype = Variable.from_node(node)
            return rtype, struct
    rv = visit_expr(node.node, Context(
        ctx=ctx,
        return_struct_cls=return_struct_cls,
        predicted_struct=node_struct
    ), macroses, config=config)
    return rv


# :class:`nodes.Literal` visitors

@visits_expr(nodes.TemplateData)
def visit_template_data(node, ctx, macroses=None, config=default_config):
    return Scalar(), Dictionary()


@visits_expr(nodes.Const)
def visit_const(node, ctx, macroses=None, config=default_config):
    ctx.meet(Scalar(), node)
    if isinstance(node.value, _compat.string_types):
        rtype = Scalar.from_node(node, constant=True)
    elif isinstance(node.value, bool):
        rtype = Scalar.from_node(node, constant=True)
    elif isinstance(node.value, (int, float, complex)):
        rtype = Scalar.from_node(node, constant=True)
    else:
        rtype = Scalar.from_node(node, constant=True)
    return rtype, Dictionary()


@visits_expr(nodes.Tuple)
def visit_tuple(node, ctx, macroses=None, config=default_config):
    ctx.meet(Tuple(None), node)

    struct = Dictionary()
    item_structs = []
    for item in node.items:
        item_rtype, item_struct = visit_expr(
            item, ctx, macroses, config=config)
        item_structs.append(item_rtype)
        struct = merge(struct, item_struct)
    rtype = Tuple.from_node(node, item_structs, constant=True)
    return rtype, struct


@visits_expr(nodes.List)
def visit_list(node, ctx, macroses=None, config=default_config):
    ctx.meet(List(Variable()), node)
    struct = Dictionary()

    predicted_struct = merge(List(Variable()), ctx.get_predicted_struct()).items
    el_rtype = None
    for item in node.items:
        item_rtype, item_struct = visit_expr(item, Context(
            predicted_struct=predicted_struct), macroses, config=config)
        struct = merge(struct, item_struct)
        if el_rtype is None:
            el_rtype = item_rtype
        else:
            el_rtype = merge_rtypes(el_rtype, item_rtype)
    rtype = List.from_node(node, el_rtype or Variable(), constant=True)
    return rtype, struct


@visits_expr(nodes.Dict)
def visit_dict(node, ctx, macroses=None, config=default_config):
    ctx = Context(predicted_struct=Variable.from_node(node))
    ctx.meet(Dictionary(), node)
    return _visit_dict(node, ctx, macroses, [(item.key, item.value) for item in node.items], config=config)

from ..macro import MacroCall
