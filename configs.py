
import platform
import pygame

WEB_MODE = platform.system().lower() == "emscripten"

MOVE_LEFT = (pygame.K_LEFT, pygame.K_a)
MOVE_RIGHT = (pygame.K_RIGHT, pygame.K_d)
MOVE_UP = (pygame.K_UP, pygame.K_w)
MOVE_DOWN = (pygame.K_DOWN, pygame.K_s)
SKIP = (pygame.K_SPACE,)

ALL_MOVE_KEYS = MOVE_LEFT + MOVE_RIGHT + MOVE_UP + MOVE_DOWN + SKIP

UNDO = (pygame.K_z,)
RESET = (pygame.K_r,)
PAUSE = (pygame.K_ESCAPE)
