# coding=UTF-8
'''
Utility functions for coersing and parsing dates.
'''

from datetime import date, time, datetime


_TIME_FORMATS = [ "%I:%M%p", "%H:%M" ]

_DATE_FORMATS = [ "%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%m/%d/%y" ]

_DATETIME_FORMATS = []
for datefmt in _DATE_FORMATS:
    for timefmt in _TIME_FORMATS:
        _DATETIME_FORMATS.append("%s %s" % (datefmt,timefmt))


def coerse(obj, defaultDate=None, defaultTime=None):
    if obj is None:
        pass
    elif isinstance(obj, datetime):
        return obj
    elif isinstance(obj, time):
        return datetime.combine(defaultDate, obj)        
    elif isinstance(obj, date):
        return datetime.combine(obj, defaultTime)
    else:
        try:
            return parse(str(obj), defaultTime=defaultTime, defaultDate=defaultDate)
        except ValueError:
            pass
    raise ValueError("Error while coersing object of type " + type(obj))


def parse(obj, defaultDate=None, defaultTime=None):
    if obj is None:
        pass
    elif isinstance(obj, str):
        for fmt in _DATE_FORMATS:
            try:
                dt = datetime.strptime(obj, fmt)
                if isinstance(defaultTime, time):
                    dt = datetime.combine(dt.date(), defaultTime)
                return dt
            except ValueError:
                pass
        for fmt in _TIME_FORMATS:
            try:
                dt = datetime.strptime(obj, fmt)
                if isinstance(defaultDate, date):
                    dt = datetime.combine(defaultDate, dt.time())
                return dt
            except ValueError:
                pass
        for fmt in _DATETIME_FORMATS:
            try:
                return datetime.strptime(obj, fmt)
            except ValueError:
                pass
    raise ValueError("Error while parsing object of type " + type(obj))
