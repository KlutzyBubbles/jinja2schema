import itertools

from .model import Scalar, Dictionary, List, Variable, Tuple
from .exceptions import MergeException
from ._compat import zip_longest


def merge(first, second, custom_merger=None):
    """Merges two variables.

    :param first: first variable
    :type first: :class:`.model.Variable`
    :param second: second variable
    :type second: :class:`.model.Variable`

    .. note::

        ``first`` must reflect expressions that occur in template **before** the expressions of ``second``.
    """
    if isinstance(first, Scalar) and isinstance(second, Scalar):
        result = first.clone()
    elif isinstance(first, Dictionary) and isinstance(second, Dictionary):
        result = Dictionary()
        for key in set(itertools.chain(first.iterkeys(), second.iterkeys())):
            if key in first and key in second:
                result[key] = merge(first[key], second[key], custom_merger=custom_merger)
            elif key in first:
                result[key] = first[key].clone()
            elif key in second:
                result[key] = second[key].clone()
    elif isinstance(first, List) and isinstance(second, List):
        result = List(merge(first.items, second.items, custom_merger=custom_merger))
    elif isinstance(first, Tuple) and isinstance(second, Tuple):
        if first.items is second.items is None:
            result = Tuple(None)
        else:
            if len(first.items) != len(second.items) and not (first.may_be_extended or second.may_be_extended):
                raise MergeException(first, second)
            result = Tuple([merge(a, b, custom_merger=custom_merger)
                            for a, b in zip_longest(first.items, second.items, fillvalue=Variable())])
    elif (isinstance(first, Tuple) or isinstance(second, Tuple)) and (isinstance(first, List) or isinstance(second, List)):
      tuple_item = first if isinstance(first, Tuple) else second
      list_item = first if isinstance(first, List) else second
      tuple_item.items = tuple_item.items if tuple_item.items is not None else ()
      if len(tuple_item.items) != len(list_item.items) and not tuple_item.may_be_extended:
        raise MergeException(tuple_item, list_item)
      result = Tuple([merge(a, b, custom_merger=custom_merger)
                            for a, b in zip_longest(tuple_item.items, tuple(list_item.items), fillvalue=Variable())])
    elif isinstance(first, Scalar) or isinstance(second, Scalar):
      scalar_item = first if isinstance(first, Scalar) else second
      other_item = first if not isinstance(first, Scalar) else second
      # print('SCALAR')
      # print(scalar_item)
      # print(other_item)
      # print('CHECKS')
      # print(isinstance(other_item, Dictionary))
      # print(isinstance(other_item, Tuple))
      # print(isinstance(other_item, List))
      # print('END')
      if instanceof_many(other_item, [List, Tuple, Dictionary]):
        raise MergeException(first, second)
      result = scalar_item.clone()
      #print('result')
      #print(result)
      #print('END')
    elif instanceof_many(first, [List, Tuple, Dictionary]) or instanceof_many(second, [List, Tuple, Dictionary]):
      typed_item = first if instanceof_many(first, [List, Tuple, Dictionary]) else second
      other_item = first if not instanceof_many(first, [List, Tuple, Dictionary]) else second
      #print('TYPED')
      #print(typed_item)
      #print(other_item)
      #print('END')
      if isinstance(other_item, Scalar):
        raise MergeException(first, second)
      result = typed_item.clone()
      #print('result')
      #print(result)
      #print('END')
    elif first.is_unknown() or second.is_unknown():
      known_item = second if first.is_unknown() else first
      result = known_item.clone()
    else:
      raise MergeException(first, second)
    result.label = first.label or second.label
    result.linenos = list(sorted(set(first.linenos + second.linenos)))
    result.constant = first.constant
    result.may_be_defined = first.may_be_defined
    result.used_with_default = first.used_with_default and second.used_with_default
    result.checked_as_defined = first.checked_as_defined and second.checked_as_defined
    result.checked_as_undefined = first.checked_as_undefined and second.checked_as_undefined
    if callable(custom_merger):
        result = custom_merger(first, second, result)
    return result

def instanceof_many(obj, instances):
  for instance in instances:
    if isinstance(obj, instance):
      return True
  return False

def merge_many(first, second, *args):
    struct = merge(first, second)
    if args:
        return merge_many(struct, *args)
    else:
        return struct


def merge_bool_expr_structs(first, second, operator=None):
    def merger(first, second, result):
        result.checked_as_defined = first.checked_as_defined
        result.checked_as_undefined = first.checked_as_undefined and second.checked_as_undefined
        return result
    return merge(first, second, custom_merger=merger)


def merge_rtypes(first, second, operator=None):
    if operator in ('+', '-'):
        if type(first) is not type(second) and not (isinstance(first, Variable) or isinstance(second, Variable)):
            raise MergeException(first, second)
    return merge(first, second)
