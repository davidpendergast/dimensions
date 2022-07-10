import src.utils as utils
import random


BLACK_ID = -1
WHITE_ID = 0

RED_ID = 1
GREEN_ID = 2
BLUE_ID = 3
PINK_ID = 4
YELLOW_ID = 5

BROWN_ID = 6

DEFAULT_COLORS = {
    BLACK_ID: ((0, 0, 0), "black"),
    WHITE_ID: ((217, 217, 217), "white"),
    RED_ID: ((255, 0, 0), "red"),
    GREEN_ID: ((40, 255, 0), "green"),
    BLUE_ID: ((66, 99, 255), "blue"),
    PINK_ID: ((255, 33, 247), "pink"),
    BROWN_ID: ((234, 185, 35), "brown"),
    YELLOW_ID: ((255, 246, 0), "yellow"),
}


def _hex_to_ints(hex_val):
    return (
        (0xFF0000 & hex_val) // 0x010000,
        (0x00FF00 & hex_val) // 0x000100,
        (0x0000FF & hex_val) // 0x000001
    )


# Based on: https://lospec.com/palette-list/ibm-color-blind-safe
# https://davidmathlogic.com/colorblind/#%23648FFF-%23725CD8-%23DC267F-%23FE6100-%23FFB000-%23D2A96A-%23FFFFFF
COLORBLIND_COLORS = {
    BLUE_ID: (_hex_to_ints(0x648fff), "blue"),
    GREEN_ID: (_hex_to_ints(0x9FF986), "green"),  # 0x785ef0),  # tweaked
    PINK_ID: (_hex_to_ints(0xdc267f), "pink"),
    RED_ID: (_hex_to_ints(0xfe6100), "red"),
    YELLOW_ID: (_hex_to_ints(0xffb000), "yellow"),
    BROWN_ID: (_hex_to_ints(0xD2A96A), "brown"),  # I added this
}


COLORS = {}


def load(colorblind=False):
    COLORS.clear()
    COLORS.update(DEFAULT_COLORS)
    if colorblind:
        COLORS.update(COLORBLIND_COLORS)


def get_color(color_id):
    if color_id in COLORS:
        return COLORS[color_id][0]
    else:
        return COLORS[WHITE_ID][0]


def get_white():
    return get_color(WHITE_ID)


def get_color_name(color_id, caps=False):
    res = "unknown"
    if color_id in COLORS:
        res = COLORS[color_id][1]
    if caps:
        return res[0].upper() + res[1:]
    else:
        return res


def rand_color_id(include_white=False, include_brown=False):
    c_list = [c for c in range(RED_ID, YELLOW_ID + 1)]
    if include_white:
        c_list.append(WHITE_ID)
    if include_brown:
        c_list.append(BROWN_ID)
    return random.choice(c_list)


def interpolate(c1, c2, a, steps=None):
    diff = utils.sub(c2, c1)
    if steps is not None:
        diff = tuple(steps * round(d * a) for d in utils.scale(diff, 1 / steps))
    else:
        diff = tuple(round(d * a) for d in diff)
    return utils.bound(utils.add(c1, diff), 0, 255)


def can_interact(c1, c2):
    if c1 == BROWN_ID or c2 == BROWN_ID:
        return True  # brown can always push or be pushed
    elif c1 == -1 or c2 == -1:
        return False  # this means out of bounds
    else:
        return c1 != c2
