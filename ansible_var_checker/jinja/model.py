import pprint

from jinja2 import nodes

from . import _compat


class Variable(object):
    """A base variable class.

    .. attribute:: linenos

        An ordered list of line numbers on which the variable occurs.

    .. attribute:: label

        A name of the variable in template.

    .. attribute:: constant

        Is true if the variable is defined using a ``{% set %}`` tag before it
        occurs within any other statement in the template, or inferred from
        a constant Jinja2 node.

    .. attribute:: may_be_defined

        Is true if the variable would be defined (using a ``{% set %}`` expression) if it's missing
        from the template context. For example, ``x`` is ``may_be_defined`` in the following template::

            {% if x is undefined %} {% set x = 1 %} {% endif %}

    .. attribute:: used_with_default

        Is true if the variable occurs only within the ``default`` filter.

    .. attribute:: checked_as_undefined

        Is true if the variable occurs within ``{% if %}`` block which condition checks
        if the variable is undefined.

    .. attribute:: checked_as_defined

        Is true if the variable occurs within ``{% if %}`` block which condition checks
        if the variable is defined.

    .. attribute:: value

        Value of the variable in template. Set by default filter or assignment.
    """
    def __init__(self, label=None, linenos=None, constant=False,
                 may_be_defined=False, used_with_default=False,
                 checked_as_undefined=False, checked_as_defined=False):
        self.label = label
        self.linenos = linenos if linenos is not None else []
        self.constant = constant
        self.may_be_defined = may_be_defined
        self.used_with_default = used_with_default
        self.checked_as_undefined = checked_as_undefined
        self.checked_as_defined = checked_as_defined

    def clone(self):
        cls = type(self)
        return cls(**self.__dict__)

    @classmethod
    def _get_kwargs_from_node(cls, node):
        return {
            'linenos': [node.lineno],
            'label': node.name if isinstance(node, nodes.Name) else None,
        }

    def _get_vals(self):
      return str(self.linenos) + ', ' + str(self.label) + ', ' + str(self.constant) + ', ' + str(self.used_with_default) + ', ' + str(self.checked_as_undefined) + ', ' + str(self.checked_as_defined) + ', ' + str(self.required)

    def is_unknown(Self):
      return True

    @classmethod
    def from_node(cls, node, **kwargs):
        """Constructs a variable using information from ``node`` (such as label and line numbers).

        :param node: NODE node
        :type node: :class:`jinja2.nodes.Node`
        """
        for k, v in list(kwargs.items()):
            if v is None:
                del kwargs[k]
        kwargs = dict(cls._get_kwargs_from_node(node), **kwargs)
        return cls(**kwargs)

    @property
    def required(self):
        return not any([self.may_be_defined, self.used_with_default,
                        self.checked_as_defined, self.checked_as_undefined])

    def __eq__(self, other):
        return (
            type(self) is type(other) and
            self.linenos == other.linenos and
            self.label == other.label and
            self.constant == other.constant and
            self.used_with_default == other.used_with_default and
            self.checked_as_undefined == other.checked_as_undefined and
            self.checked_as_defined == other.checked_as_defined and
            self.required == other.required
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
      return '<unknown>, ' + self._get_vals()


class Dictionary(Variable):
    """A dictionary.

    Implements some methods of Python :class:`dict`.

    .. automethod:: __setitem__
    .. automethod:: __getitem__
    .. automethod:: __delitem__
    .. automethod:: get
    .. automethod:: items
    .. automethod:: iteritems
    .. automethod:: keys
    .. automethod:: iterkeys
    .. automethod:: pop
    """

    def __init__(self, data=None, **kwargs):
        self.data = data or {}
        super(Dictionary, self).__init__(**kwargs)

    def __eq__(self, other):
        return super(Dictionary, self).__eq__(other) and self.data == other.data

    def __repr__(self):
        return pprint.pformat(self.data) + ', ' + self._get_vals()

    def clone(self):
        rv = super(Dictionary, self).clone()
        rv.data = {}
        for k, v in _compat.iteritems(self.data):
            rv.data[k] = v.clone()
        return rv

    def is_unknown(Self):
      return False

    @classmethod
    def from_node(cls, node, data=None, **kwargs):
        kwargs = dict(cls._get_kwargs_from_node(node), **kwargs)
        return cls(data, **kwargs)

    def __setitem__(self, key, value):
        self.data[key] = value

    def __getitem__(self, key):
        return self.data[key]

    def __delitem__(self, key):
        del self.data[key]

    def __contains__(self, key):
        return key in self.data

    def get(self, name, default=None):
        if name in self:
            return self[name]
        else:
            return default

    def items(self):
        return self.data.items()

    def iteritems(self):
        return _compat.iteritems(self.data)

    def keys(self):
        return self.data.keys()

    def iterkeys(self):
        return _compat.iterkeys(self.data)

    def pop(self, key, default=None):
        return self.data.pop(key, default)


class List(Variable):
    """A list which items are of the same type.

    .. attribute:: items

        A structure of list items, subclass of :class:`Variable`.
    """
    def __init__(self, items, **kwargs):
        self.items = items
        super(List, self).__init__(**kwargs)

    def __eq__(self, other):
        return super(List, self).__eq__(other) and self.items == other.items

    def __repr__(self):
        return pprint.pformat([self.items]) + ', ' + self._get_vals()

    def clone(self):
        rv = super(List, self).clone()
        rv.items = self.items.clone()
        return rv

    def is_unknown(Self):
      return False

    @classmethod
    def from_node(cls, node, items, **kwargs):
        kwargs = dict(cls._get_kwargs_from_node(node), **kwargs)
        return cls(items, **kwargs)


class Tuple(Variable):
    """A tuple.

    .. attribute:: items

        A :class:`tuple` of :class:`Variable` instances or ``None`` if the tuple items are unknown.

    .. attribute:: items

        Whether new elements can be added to the tuple in the process of merge or not.
    """
    def __init__(self, items, **kwargs):
        self.items = tuple(items) if items is not None else ()
        self.may_be_extended = kwargs.pop('may_be_extended', False)
        super(Tuple, self).__init__(**kwargs)

    def __eq__(self, other):
        return super(Tuple, self).__eq__(other) and self.items == other.items

    def __repr__(self):
        return pprint.pformat(self.items) + ', ' + self._get_vals()

    def clone(self):
        rv = super(Tuple, self).clone()
        rv.items = self.items and tuple(s.clone() for s in self.items)
        return rv

    def is_unknown(Self):
      return False

    @classmethod
    def from_node(cls, node, items, **kwargs):
        kwargs = dict(cls._get_kwargs_from_node(node), **kwargs)
        return cls(items, **kwargs)


class Scalar(Variable):
    """A scalar. Either string, number, boolean or ``None``."""
    def __repr__(self):
        return '<scalar>, ' + self._get_vals()

    def is_unknown(Self):
      return False
