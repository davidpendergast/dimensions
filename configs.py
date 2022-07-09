
import platform
import pygame

WEB_MODE = platform.system().lower() == "emscripten"

COLORBLIND_MODE = True
COLORBLIND_TOGGLE = (pygame.K_c,)

SONG_VOLUME = 1.0
SONG_MUTED = False

SOUND_VOLUME = 0.2
SOUND_MUTED = False


MOVE_LEFT = (pygame.K_LEFT, pygame.K_a)
MOVE_RIGHT = (pygame.K_RIGHT, pygame.K_d)
MOVE_UP = (pygame.K_UP, pygame.K_w)
MOVE_DOWN = (pygame.K_DOWN, pygame.K_s)
SKIP = (pygame.K_SPACE,)

ALL_MOVE_KEYS = MOVE_LEFT + MOVE_RIGHT + MOVE_UP + MOVE_DOWN + SKIP

UNDO = (pygame.K_z,)
RESET = (pygame.K_r,)
PAUSE = (pygame.K_ESCAPE,)
