import os.path
import platform
import pygame

VERSION = "1.0.0"
WEB_MODE = platform.system().lower() == "emscripten"

COLORBLIND_MODE = True
COLORBLIND_TOGGLE = (pygame.K_c,)

SONG_VOLUME = 1.0
SONG_MUTED = False  # TODO unmute
MUSIC_TOGGLE = (pygame.K_m,)

SOUND_VOLUME = 0.2
SOUND_MUTED = False


MOVE_LEFT = (pygame.K_LEFT, pygame.K_a)
MOVE_RIGHT = (pygame.K_RIGHT, pygame.K_d)
MOVE_UP = (pygame.K_UP, pygame.K_w)
MOVE_DOWN = (pygame.K_DOWN, pygame.K_s)

ALL_MOVE_KEYS = MOVE_LEFT + MOVE_RIGHT + MOVE_UP + MOVE_DOWN

ENTER = (pygame.K_RETURN,)
ESCAPE = (pygame.K_ESCAPE,)
UNDO = (pygame.K_z, pygame.K_BACKSPACE)
RESET = (pygame.K_r, pygame.K_RETURN)
PAUSE = (pygame.K_ESCAPE,)

# debug stuff
IS_DEBUG = not WEB_MODE and os.path.exists(".gitignore")
DEBUG_FAKE_LEVELS = False
DEBUG_NO_CONTINUE = False
DEBUG_ALL_UNLOCKED = True
DEBUG_OVERWRITE_WHILE_SAVING = True
