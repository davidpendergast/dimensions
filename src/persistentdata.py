import traceback

import configs
import json

import src.utils as utils

if configs.WEB_MODE:
    # note that this stuff only resolves when running in a web context
    if __WASM__ and __EMSCRIPTEN__ and __EMSCRIPTEN__.is_browser:
        from __EMSCRIPTEN__ import window, document


VERSION_KEY = "_vers"

_KEY = "alienknightmare_data"
_IN_MEMORY = {
    VERSION_KEY: configs.VERSION
}
_DIRTY = False


def load_data_from_disk() -> bool:
    global _IN_MEMORY, _DIRTY
    _IN_MEMORY = {}
    _DIRTY = False

    try:
        if configs.WEB_MODE:
            blob_str = window.localStorage.getItem(_KEY)
            if blob_str is not None:
                print(f"INFO: loaded \"{_KEY}\" from window.localStorage: {blob_str}")
                _IN_MEMORY = json.loads(blob_str)
        else:
            pass  # TODO other modes?
    except:
        print("ERROR: failed to load persistent data")
        traceback.print_exc()
        return False

    return True


def save_data_to_disk(force=False) -> bool:
    global _DIRTY
    if _DIRTY or force:
        _IN_MEMORY[VERSION_KEY] = configs.VERSION
        _DIRTY = False

        try:
            blob_str = json.dumps(_IN_MEMORY)
            if configs.WEB_MODE:
                window.localStorage.setItem(_KEY, blob_str)
                print(f"INFO: wrote \"{_KEY}\" to window.localStorage: {blob_str}")
        except:
            print("ERROR: failed to save persistent data")
            traceback.print_exc()
            return False
    return True


def reset_data(hard=False):
    global _DIRTY
    _IN_MEMORY.clear()
    _DIRTY = False

    if hard:
        try:
            if configs.WEB_MODE:
                window.localStorage.removeItem(_KEY)
        except:
            print("ERROR: failed to clear persistent data on-disk")
            traceback.print_exc()
            return False

    return True


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
