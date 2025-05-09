"""defines generic type conversion functions, as used in bind and result
processors.

They all share one common characteristic: None is passed through unchanged.

"""

import codecs
import datetime
import re

from sqlalchemy import util


def str_to_datetime_processor_factory(regexp, type_):
    rmatch = regexp.match
    # Even on python2.6 datetime.strptime is both slower than this code
    # and it does not support microseconds.
    has_named_groups = bool(regexp.groupindex)

    def process(value):
        if value is None:
            return None
        else:
            try:
                m = rmatch(value)
            except TypeError as err:
                util.raise_(
                    ValueError(
                        "Couldn't parse %s string '%r' "
                        "- value is not a string." % (type_.__name__, value)
                    ),
                    from_=err,
                )
            if m is None:
                raise ValueError(
                    "Couldn't parse %s string: "
                    "'%s'" % (type_.__name__, value)
                )
            if has_named_groups:
                groups = m.groupdict(0)
                return type_(
                    **dict(
                        list(
                            zip(
                                iter(groups.keys()),
                                list(map(int, iter(groups.values()))),
                            )
                        )
                    )
                )
            else:
                return type_(*list(map(int, m.groups(0))))

    return process


def py_fallback():
    def to_unicode_processor_factory(encoding, errors=None):
        decoder = codecs.getdecoder(encoding)

        def process(value):
            if value is None:
                return None
            else:
                # decoder returns a tuple: (value, len). Simply dropping the
                # len part is safe: it is done that way in the normal
                # 'xx'.decode(encoding) code path.
                return decoder(value, errors)[0]

        return process

    def to_conditional_unicode_processor_factory(encoding, errors=None):
        decoder = codecs.getdecoder(encoding)

        def process(value):
            if value is None:
                return None
            elif isinstance(value, util.text_type):
                return value
            else:
                # decoder returns a tuple: (value, len). Simply dropping the
                # len part is safe: it is done that way in the normal
                # 'xx'.decode(encoding) code path.
                return decoder(value, errors)[0]

        return process

    def to_decimal_processor_factory(target_class, scale):
        fstring = "%%.%df" % scale

        def process(value):
            if value is None:
                return None
            else:
                return target_class(fstring % value)

        return process

    def to_float(value):  # noqa
        if value is None:
            return None
        else:
            return float(value)

    def to_str(value):  # noqa
        if value is None:
            return None
        else:
            return str(value)

    def int_to_boolean(value):  # noqa
        if value is None:
            return None
        else:
            return bool(value)

    DATETIME_RE = re.compile(
        r"(\d+)-(\d+)-(\d+) (\d+):(\d+):(\d+)(?:\.(\d+))?"
    )
    TIME_RE = re.compile(r"(\d+):(\d+):(\d+)(?:\.(\d+))?")
    DATE_RE = re.compile(r"(\d+)-(\d+)-(\d+)")

    str_to_datetime = str_to_datetime_processor_factory(  # noqa
        DATETIME_RE, datetime.datetime
    )
    str_to_time = str_to_datetime_processor_factory(  # noqa
        TIME_RE, datetime.time
    )  # noqa
    str_to_date = str_to_datetime_processor_factory(  # noqa
        DATE_RE, datetime.date
    )  # noqa
    return locals()
