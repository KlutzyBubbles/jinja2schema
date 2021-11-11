class InferException(Exception):
    """Base class for jinja2schema exceptions."""

class MergeException(InferException):
    """Conflict of merging two structures.

    .. attribute:: fst

        :class:`Variable`

    .. attribute:: snd

        :class:`Variable`
    """
    def __init__(self, fst, snd):
        self.fst = fst
        self.snd = snd

    def __str__(self):
        get_label = lambda s: 'unnamed variable' if s.label is None else 'variable "{0}"'.format(s.label)
        def get_usage(s):
            return s.__class__.__name__.lower()
        get_linenos = lambda s: ', '.join(map(str, s.linenos))
        return ('{fst_label} (used as {fst_usage} on lines {fst_linenos}) conflicts with '
                '{snd_label} (used as {snd_usage} on lines: {snd_linenos})').format(
                    fst_label=get_label(self.fst), snd_label=get_label(self.snd),
                    fst_usage=get_usage(self.fst), snd_usage=get_usage(self.snd),
                    fst_linenos=get_linenos(self.fst), snd_linenos=get_linenos(self.snd))

class UnexpectedExpression(InferException):
    """Raised when a visitor was expecting compatibility with :attr:`expected_struct`,
    but got :attr:`actual_node` of structure :attr:`actual_struct`.

    Compatibility is checked by merging expected structure with actual one.

    .. attribute:: expected_struct

        expected :class:`.model.Variable`

    .. attribute:: actual_node

        actual :class:`jinja2.nodes.Node`

    .. attribute:: actual_node

        :class:`.model.Variable` described by ``actual_node``
    """
    def __init__(self, expected_struct, actual_node, actual_struct):
        self.expected_struct = expected_struct
        self.actual_node = actual_node
        self.actual_struct = actual_struct

    def __str__(self):
        return ('conflict on the line {lineno}\n'
                'got: NODE node jinja2.nodes.{node} of structure {actual_struct}\n'
                'expected structure: {expected_struct}').format(
                    lineno=self.actual_node.lineno,
                    node=self.actual_node.__class__.__name__,
                    actual_struct=self.actual_struct,
                    expected_struct=self.expected_struct)

class InvalidExpression(InferException):
    """Raised when a template uses Jinja2 features that are not supported by the library
    or when a template contains incorrect expressions (i.e., such as applying ``divisibleby`` filter
    without an argument).

    .. attribute:: node

        :class:`jinja2.nodes.Node` caused the exception
    """
    def __init__(self, node, message):
        self.node = node
        self.message = message

    def __str__(self):
        return 'line {0}: {1}'.format(self.node.lineno, self.message)
