import math

import configs

import sys
import os
import typing
import json


def asset_path(filepath):
    if configs.WEB_MODE:
        return filepath
    elif getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, filepath)
    else:
        return filepath


def add(t1, t2):
    return tuple(i1 + i2 for i1, i2 in zip(t1, t2))


def sub(t1, t2):
    return tuple(i1 - i2 for i1, i2 in zip(t1, t2))


def scale(t1, a):
    return tuple(i * a for i in t1)


def bound(t, lower, upper):
    return tuple(min(max(lower, i), upper) for i in t)


def round(t):
    return tuple(int(i + 0.5) if i >= 0 else int(i - 0.5) for i in t)


def dist_sq(t1, t2):
    d = 0
    for i1, i2 in zip(t1, t2):
        d += (i2 - i1) * (i2 - i1)
    return d


def dist(t1, t2):
    return math.sqrt(dist_sq(t1, t2))


def mag_sq(t1):
    d = 0
    for i in t1:
        d += i * i
    return d


def mag(t):
    return math.sqrt(mag_sq(t))


def set_length(t, length):
    m = mag(t)
    if len(t) == 0:
        return ()
    elif m == 0:
        # you get (l, 0, 0, 0, 0, ...)
        return tuple([length] + [0] * (len(t) - 1))
    else:
        return scale(t, length / m)


def rect_contains(rect, xy) -> bool:
    return not (xy[0] < rect[0]
                or xy[1] < rect[1]
                or xy[0] >= rect[0] + rect[2]
                or xy[1] >= rect[1] + rect[3])


def expand_rect(rect, amt):
    return (rect[0] - amt, rect[1] - amt, rect[2] + amt * 2, rect[3] + amt * 2)


def get_rect_containing_points(pts) -> typing.Tuple[int, int, int, int]:
    if len(pts) == 0:
        return 0, 0, 0, 0
    else:
        min_x = min(map(lambda pt: pt[0], pts))
        min_y = min(map(lambda pt: pt[1], pts))
        max_x = max(map(lambda pt: pt[0], pts))
        max_y = max(map(lambda pt: pt[1], pts))

        return min_x, min_y, max_x - min_x + 1, max_y - min_y + 1


def rect_center(rect):
    return rect[0] + rect[2] / 2, rect[1] + rect[3] / 2


def interpolate(t1, t2, a, rounded=False):
    if rounded:
        return tuple(round(i1 + a * (i2 - i1)) for i1, i2 in zip(t1, t2))
    else:
        return tuple(i1 + a * (i2 - i1) for i1, i2 in zip(t1, t2))


def copy_json(blob):
    return json.loads(json.dumps(blob))  # pog


def contains_type(iterable, types):
    return any(x for x in iterable if isinstance(x, types))


def get_dict_type_coercer(key_type, val_type):
    def _coerce(d):
        keys_to_del = set()
        for k in d:
            if not isinstance(k, key_type):
                keys_to_del.add(k)
            elif not isinstance(d[k], val_type):
                keys_to_del.add(k)
        if len(keys_to_del) > 0:
            return {k: d[k] for k in d if k not in keys_to_del}
        else:
            return d
    return _coerce
