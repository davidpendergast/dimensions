import traceback

import configs
import json

import src.utils as utils

VERSION_KEY = "_vers"

_KEY = "alienknightmare_data"
_IN_MEMORY = {
    VERSION_KEY: configs.VERSION
}
_DIRTY = False


def load_data_from_disk():
    global _IN_MEMORY, _DIRTY
    _IN_MEMORY = {}  # TODO load it
    _DIRTY = False


def save_data_to_disk(force=False):
    global _DIRTY
    if _DIRTY or force:
        _IN_MEMORY[VERSION_KEY] = configs.VERSION
        as_text = json.dumps(_IN_MEMORY)
        # TODO save it
        _DIRTY = False


def get_data(key, coercer=None, or_else=None):
    if key in _IN_MEMORY:
        val = _IN_MEMORY[key]
        val = utils.copy_json(val)
        if coercer is not None:
            try:
                return coercer(val)
            except ValueError:
                print(f"ERROR: failed to coerce persistent data: {key}={val} (using {or_else} instead)")
                traceback.print_exc()

    return or_else


def set_data(key, val, and_save_to_disk=True):
    global _IN_MEMORY, _DIRTY
    val = utils.copy_json(val)
    if key not in _IN_MEMORY or _IN_MEMORY[key] != val:
        _DIRTY = True
    _IN_MEMORY[key] = val

    if and_save_to_disk:
        save_data_to_disk()
