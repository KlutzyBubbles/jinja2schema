import sys

PY2 = sys.version_info[0] == 2

if not PY2:
    string_types = (str,)

    iterkeys = lambda d: iter(d.keys())
    itervalues = lambda d: iter(d.values())
    iteritems = lambda d: iter(d.items())

    izip = zip

    from itertools import zip_longest
else:
    string_types = (str, unicode)

    iterkeys = lambda d: d.iterkeys()
    itervalues = lambda d: d.itervalues()
    iteritems = lambda d: d.iteritems()

    from itertools import izip

    from itertools import izip_longest as zip_longest
