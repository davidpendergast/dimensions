import typing

import pygame

CUR_TIME = 0
CUR_TICK = 0

HELD_KEYS: typing.Dict[int, float] = {}
PRESSED_KEYS: typing.Set[int] = set()
RELEASED_KEYS: typing.Set[int] = set()

MOUSE_POS: typing.Optional[typing.Tuple[int, int]] = None
PRESSED_MOUSE_BUTTONS: typing.Set[int] = set()


def key_down(key_id):
    HELD_KEYS[key_id] = CUR_TIME
    PRESSED_KEYS.add(key_id)


def key_up(key_id):
    if key_id in HELD_KEYS:
        del HELD_KEYS[key_id]
    RELEASED_KEYS.add(key_id)


def mouse_button_down(btn):
    PRESSED_MOUSE_BUTTONS.add(btn)


def mouse_moved(pos):
    global MOUSE_POS
    MOUSE_POS = pos


def new_frame(cur_time):
    global CUR_TIME, CUR_TICK
    CUR_TIME = cur_time
    CUR_TICK += 1

    PRESSED_KEYS.clear()
    RELEASED_KEYS.clear()
    PRESSED_MOUSE_BUTTONS.clear()


def get_time() -> float:
    return CUR_TIME


def get_ticks() -> int:
    return CUR_TICK


def was_pressed(keys) -> bool:
    if isinstance(keys, int):
        return keys in PRESSED_KEYS
    else:
        for k in keys:
            if k in PRESSED_KEYS:
                return True
        return False


def is_held(keys, thresh=0) -> bool:
    if isinstance(keys, int):
        return keys in HELD_KEYS and CUR_TIME - HELD_KEYS[keys] >= thresh
    else:
        for k in keys:
            if k in HELD_KEYS and CUR_TIME - HELD_KEYS[keys] >= thresh:
                return True
        return False


def get_mouse_pos() -> typing.Optional[typing.Tuple[int, int]]:
    return MOUSE_POS


def did_click(btn=1, in_rect: typing.Optional[pygame.Rect] = None) -> bool:
    if btn in PRESSED_MOUSE_BUTTONS and MOUSE_POS is not None:
        return in_rect is None or in_rect.collidepoint(*MOUSE_POS)



