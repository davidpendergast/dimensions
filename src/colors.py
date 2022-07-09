
BLACK_ID = -1
WHITE_ID = 0

RED_ID = 1
GREEN_ID = 2
BLUE_ID = 3
PINK_ID = 4
YELLOW_ID = 5

BROWN_ID = 6

DEFAULT_COLORS = {
    BLACK_ID: (0, 0, 0),
    WHITE_ID: (217, 217, 217),
    RED_ID: (255, 0, 0),
    GREEN_ID: (40, 255, 0),
    BLUE_ID: (66, 99, 255),
    PINK_ID: (255, 33, 247),
    BROWN_ID: (234, 185, 35),
    YELLOW_ID: (255, 246, 0),
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
    BLUE_ID: _hex_to_ints(0x648fff),
    GREEN_ID: _hex_to_ints(0x9FF986),  # 0x785ef0),  # tweaked
    PINK_ID: _hex_to_ints(0xdc267f),
    RED_ID: _hex_to_ints(0xfe6100),
    YELLOW_ID: _hex_to_ints(0xffb000),
    BROWN_ID: _hex_to_ints(0xD2A96A)  # I added this
}


COLORS = {}


def load(colorblind=False):
    COLORS.clear()
    COLORS.update(DEFAULT_COLORS)
    if colorblind:
        COLORS.update(COLORBLIND_COLORS)


def get_color(color_id):
    if color_id in COLORS:
        return COLORS[color_id]
    else:
        return 0, 0, 0
