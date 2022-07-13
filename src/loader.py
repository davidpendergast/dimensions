import os
import json
import random
import string

import configs
import src.level as level
import src.colors as colors
import src.utils as utils
import src.persistentdata as pd


_ORDERED_LEVELS_FROM_DISK = []
_NAME_TO_LEVEL = {}

EASTER_EGG_NAME = None
EASTER_EGG_LEVEL = None
SAW_SNEK_LORE = False

LEVEL_COMPLETIONS_KEY = "completed_levels"


def load_levels():
    _ORDERED_LEVELS_FROM_DISK.clear()
    _NAME_TO_LEVEL.clear()

    if configs.IS_DEBUG and configs.DEBUG_FAKE_LEVELS:
        for _ in range(24):
            l = make_demo_state2()
            _ORDERED_LEVELS_FROM_DISK.append(l)
            _NAME_TO_LEVEL[l.name] = l
    else:
        base_path = utils.asset_path("assets/levels")
        for fname in sorted(os.listdir(base_path)):
            if fname.endswith(".json"):
                filepath = os.path.join(base_path, fname)
                with open(filepath, 'r') as f:
                    try:
                        l = level.from_json(json.load(f))
                        l.original_filepath = filepath
                        _ORDERED_LEVELS_FROM_DISK.append(l)
                        _NAME_TO_LEVEL[l.name] = l
                        print(f"INFO: loaded '{l.name}' from {filepath}")
                    except Exception as e:
                        print(f"ERROR: failed to load: {filepath}")
                        raise e

        _make_easter_egg_level("First Contact")


def num_levels() -> int:
    return len(_ORDERED_LEVELS_FROM_DISK)


def get_level_by_idx(idx) -> level.State:
    return _ORDERED_LEVELS_FROM_DISK[idx]


def get_level_by_name(name) -> level.State:
    return _NAME_TO_LEVEL[name]


def idx_of(name: str) -> int:
    for idx, lvl in enumerate(_ORDERED_LEVELS_FROM_DISK):
        if lvl.name == name:
            return idx
    if name is not None and name == EASTER_EGG_NAME:
        return 0
    return -1


def all_levels():
    for l in _ORDERED_LEVELS_FROM_DISK:
        yield l


def is_completed(name) -> int:
    completed_levels = pd.get_data(LEVEL_COMPLETIONS_KEY, coercer=utils.get_dict_type_coercer(str, int), or_else={})
    if name in completed_levels:
        return completed_levels[name]
    else:
        return 0


def set_completed(name, steps):
    completed_levels = pd.get_data(LEVEL_COMPLETIONS_KEY, coercer=utils.get_dict_type_coercer(str, int), or_else={})
    if name not in completed_levels or completed_levels[name] > steps:
        completed_levels[name] = steps
        pd.set_data(LEVEL_COMPLETIONS_KEY, completed_levels)


def is_every_level_complete():
    for l in all_levels():
        if not is_completed(l.name):
            return False
    return True


def get_total_steps() -> int:
    completed_levels = pd.get_data(LEVEL_COMPLETIONS_KEY, coercer=utils.get_dict_type_coercer(str, int), or_else={})
    res = 0
    for name in completed_levels:
        res += int(completed_levels[name])
    return res


def _make_easter_egg_level(base_level_name):
    global EASTER_EGG_LEVEL, EASTER_EGG_NAME
    EASTER_EGG_NAME = base_level_name + " (s)"

    if base_level_name in _NAME_TO_LEVEL:
        EASTER_EGG_LEVEL = _NAME_TO_LEVEL[base_level_name].copy()
        EASTER_EGG_LEVEL.name = EASTER_EGG_NAME
        snek_xy = (7, 2)
        if EASTER_EGG_LEVEL.is_in_bounds(snek_xy):
            EASTER_EGG_LEVEL.add_entity(snek_xy, level.Snek())
        _NAME_TO_LEVEL[EASTER_EGG_NAME] = EASTER_EGG_LEVEL
    return EASTER_EGG_LEVEL


def make_demo_state():
    state = level.State("Demo")
    state.add_entity((4, 4), level.Player(colors.RED_ID))
    state.add_entity((5, 2), level.Wall())
    state.add_entity((5, 3), level.Wall())
    state.add_entity((5, 4), level.Wall())
    state.add_entity((6, 4), level.Wall())
    state.add_entity((7, 4), level.Wall())
    state.add_entity((6, 5), level.Enemy(colors.GREEN_ID, (-1, 0)))
    state.add_entity((2, 5), level.Box())
    state.add_entity((3, 6), level.Box())
    state.add_entity((5, 7), level.Box())
    state.add_entity((8, 5), level.Potion(colors.PINK_ID))

    state.get_area(cache=True)
    return state


def make_demo_state2(dims=(13, 7)):
    import random

    name = "".join(random.choice(string.ascii_lowercase) for _2 in range(6))
    state = level.State(name)

    for x in range(dims[0]):
        for y in range(dims[1]):
            xy = (x, y)
            if x == 0 or y == 0 or x == dims[0] - 1 or y == dims[1] - 1 or random.random() < 0.2:
                if random.random() < 0.1:
                    wall_color_id = colors.rand_color_id()
                else:
                    wall_color_id = colors.WHITE_ID
                state.add_entity(xy, level.Wall(color_id=wall_color_id))
            elif random.random() < 0.2:
                if random.random() < 0.8:
                    box_color_id = random.randint(0, colors.YELLOW_ID)
                else:
                    box_color_id = colors.BROWN_ID
                state.add_entity(xy, level.Box(color_id=box_color_id))
            elif random.random() <= 0.1:
                state.add_entity(xy, level.Potion(random.randint(0, colors.YELLOW_ID)))
            elif random.random() <= 0.1:
                direction = random.choice([(-1, 0), (1, 0), (0, 1), (0, -1), (0, 0)])
                state.add_entity(xy, level.Enemy(random.randint(0, colors.YELLOW_ID), direction))

    p_xy = random.randint(1, dims[0] - 2), random.randint(1, dims[1] - 2)
    for e in list(state.all_entities_at(p_xy)):
        state.remove_entity(p_xy, e)
    state.add_entity(p_xy, level.Player(colors.RED_ID))
    state.get_area(cache=True)

    return state


def make_demo_from_json():
    return level.from_json(level.sample_blob)
