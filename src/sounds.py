import pygame

import random
import os
import traceback
import typing

import src.inputs as inputs
import src.utils as utils

_SOUNDS: typing.Dict[str, typing.List[pygame.mixer.Sound]] = {}
_TIMES_PLAYED: typing.Dict[str, float] = {}


def load():
    _SOUNDS.clear()

    base_path = utils.asset_path("assets/sounds")
    for name in os.listdir(base_path):
        if name.endswith(".wav") or name.endswith(".ogg"):
            filepath = os.path.join(base_path, name)

            prefix = name[:name.index(".")]
            if "(" in prefix:
                prefix = prefix[:prefix.index("(")]

            print(f"INFO: loading {filepath} (as '{prefix}')")
            if prefix not in _SOUNDS:
                _SOUNDS[prefix] = []

            try:
                _SOUNDS[prefix].append(pygame.mixer.Sound(filepath))
            except (IOError, pygame.error):
                print(f"ERROR: failed to load {filepath}")
                traceback.print_exc()


def play(name):
    cur_time = inputs.get_time()
    if name in _TIMES_PLAYED and cur_time == _TIMES_PLAYED[name]:
        pass  # already played this sound this frame
    elif name in _SOUNDS and len(_SOUNDS[name]) > 0:
        _TIMES_PLAYED[name] = cur_time
        to_play = random.choice(_SOUNDS[name])
        to_play.play()

