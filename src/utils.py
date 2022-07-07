import configs
import sys
import os


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


