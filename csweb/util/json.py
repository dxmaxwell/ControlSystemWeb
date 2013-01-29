# coding=UTF-8
'''
Utility classes for JSON stringify.
'''

from __future__ import absolute_import

import math, json


def stringify(obj, sanitize=True):
    if sanitize:
        obj = _sanitize(obj)
    return json.dumps(obj, allow_nan=False)


def parse(obj):
    return json.loads(obj)


def _sanitize(obj, level=0):
    if obj is None:
        return obj

    elif isinstance(obj, (str, int)):
        return obj

    elif isinstance(obj, float):
        if math.isnan(obj):
            return 'NaN'

        elif math.isinf(obj):
            if obj >= 0.0:
                return 'Infinity'
            else:
                return '-Infinity'

        else:
            return obj

    elif isinstance(obj, dict):
        result = {}
        for k, v in obj.items():
            result[k] = _sanitize(v, level+1)
        return result

    elif isinstance(obj, (tuple,list)):
        result = []
        for v in obj:
            result.append(_sanitize(v, level+1))
        return result

    else:
        raise TypeError("Sanitization of type %s not supported" % (type(obj),))
