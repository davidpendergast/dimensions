import pygame

import random
import os
import traceback
import typing

import configs
import src.inputs as inputs
import src.utils as utils

_SOUNDS: typing.Dict[str, typing.List[pygame.mixer.Sound]] = {}
_TIMES_PLAYED: typing.Dict[str, float] = {}


BOX_MOVED = "box_move"
PLAYER_MOVED = "move"
ENEMY_MOVED = "move"
PLAYER_KILLED = "synth"
PLAYER_SKIPPED = "move"
ENEMY_KILLED = "synth"
POTION_CRUSHED = "click"
POTION_CONSUMED = "powerup"


def load():
    _SOUNDS.clear()

    base_path = utils.asset_path("assets/sounds")
    for name in os.listdir(base_path):
        if name.endswith(".wav") or name.endswith(".ogg"):
            filepath = os.path.join(base_path, name)

            prefix = name[:name.index(".")].lower()
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
    if name is None:
        return
    cur_time = inputs.get_time()
    if name in _TIMES_PLAYED and cur_time == _TIMES_PLAYED[name]:
        pass  # already played this sound this frame
    elif configs.SOUND_MUTED or configs.SOUND_VOLUME <= 0:
        pass
    elif name in _SOUNDS and len(_SOUNDS[name]) > 0:
        _TIMES_PLAYED[name] = cur_time
        to_play = random.choice(_SOUNDS[name])
        to_play.set_volume(configs.SOUND_VOLUME)
        to_play.play()
    else:
        print(f"WARN: unrecognized sound id: {name}")


_SONGS = {
    "mysterious": "4-Rrapo-Taho-Mysterious-Answers.ogg"
}

MAIN_SONG = 'mysterious'


def play_song(name, loops=-1):
    if name in _SONGS:
        base_path = utils.asset_path("assets/songs")
        filepath = os.path.join(base_path, _SONGS[name])
        try:
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.set_volume(configs.SONG_VOLUME)
            pygame.mixer.music.play(loops=loops)
        except (IOError, pygame.error):
            print(f"ERROR: failed to load long {filepath}")
            traceback.print_exc()
    elif name is None:
        pygame.mixer.music.stop()
    else:
        raise ValueError(f"unrecognized song id: {name}")


def set_song_volume(vol):
    configs.SONG_VOLUME = vol
    pygame.mixer.music.set_volume(vol if not configs.SONG_MUTED else 0)


def set_sound_volume(vol):
    configs.SOUND_VOLUME = vol


def set_songs_muted(muted):
    configs.SONG_MUTED = muted
    pygame.mixer.music.set_volume(configs.SONG_VOLUME if not configs.SONG_MUTED else 0)


def set_sounds_muted(muted):
    configs.SOUND_MUTED = muted


