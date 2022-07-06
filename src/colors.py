
WHITE_ID = 0
RED_ID = 1
GREEN_ID = 2
BLUE_ID = 3
PINK_ID = 4
BROWN_ID = 5
YELLOW_ID = 6

COLORS = {
    WHITE_ID: (217, 217, 217),
    RED_ID: (255, 0, 0),
    GREEN_ID: (40, 255, 0),
    BLUE_ID: (66, 99, 255),
    PINK_ID: (255, 33, 247),
    BROWN_ID: (234, 185, 35),
    YELLOW_ID: (255, 246, 0),
}


def get_color(color_id):
    if color_id in COLORS:
        return COLORS[color_id]
    else:
        return 0, 0, 0
