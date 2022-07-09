import typing

import pygame
import src.utils as utils

CUR_TIME = 0
CUR_TICK = 0

QUIT_REQUESTED = False

HELD_KEYS: typing.Dict[int, float] = {}
PRESSED_KEYS: typing.Set[int] = set()
RELEASED_KEYS: typing.Set[int] = set()

MOUSE_POS: typing.Optional[typing.Tuple[int, int]] = None
MOUSE_MOVED_THIS_FRAME = False
PRESSED_MOUSE_BUTTONS: typing.Set[int] = set()


def send_key_down(key_id):
    HELD_KEYS[key_id] = CUR_TIME
    PRESSED_KEYS.add(key_id)


def send_key_up(key_id):
    if key_id in HELD_KEYS:
        del HELD_KEYS[key_id]
    RELEASED_KEYS.add(key_id)


def send_mouse_button_down(btn):
    PRESSED_MOUSE_BUTTONS.add(btn)


def send_mouse_moved(pos):
    global MOUSE_POS, MOUSE_MOVED_THIS_FRAME
    MOUSE_POS = pos
    MOUSE_MOVED_THIS_FRAME = True


def send_quit_signal():
    global QUIT_REQUESTED
    QUIT_REQUESTED = True


def was_quit_requested():
    return QUIT_REQUESTED


def new_frame(cur_time):
    global CUR_TIME, CUR_TICK, MOUSE_MOVED_THIS_FRAME
    CUR_TIME = cur_time
    CUR_TICK += 1

    PRESSED_KEYS.clear()
    RELEASED_KEYS.clear()
    PRESSED_MOUSE_BUTTONS.clear()
    MOUSE_MOVED_THIS_FRAME = False


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


def did_click(btn=1, in_rect=None) -> bool:
    if isinstance(btn, int):
        if btn == -1:
            btn = (1, 2, 3)  # -1 means any click
        else:
            btn = (btn,)
    for b in btn:
        if b in PRESSED_MOUSE_BUTTONS and MOUSE_POS is not None:
            return in_rect is None or utils.rect_contains(in_rect, MOUSE_POS)


def did_mouse_move() -> bool:
    return MOUSE_MOVED_THIS_FRAME and get_mouse_pos() is not None



