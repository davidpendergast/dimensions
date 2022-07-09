import pygame
import asyncio

import configs
import src.inputs as inputs
import src.level as level
import src.colors as colors
import src.rendering as rendering

import src.sprites as sprites
import src.sounds as sounds


def make_demo_state():
    state = level.State("Demo")

    state.add_entity((4, 4), level.Player(colors.RED_ID))
    state.add_entity((5, 2), level.Wall())
    state.add_entity((5, 3), level.Wall())
    state.add_entity((5, 4), level.Wall())
    state.add_entity((6, 4), level.Wall())
    state.add_entity((7, 4), level.Wall())
    state.add_entity((6, 5), level.Enemy(colors.GREEN_ID, (-1, 0)))
    state.add_entity((2, 5), level.Box())
    state.add_entity((3, 6), level.Box())
    state.add_entity((5, 7), level.Box())
    state.add_entity((8, 5), level.Potion(colors.PINK_ID))

    return state


def make_demo_state2(dims):
    import random

    state = level.State("Demo 2")
    for x in range(dims[0]):
        for y in range(dims[1]):
            xy = (x, y)
            if x == 0 or y == 0 or x == dims[0] - 1 or y == dims[1] - 1 or random.random() < 0.2:
                state.add_entity(xy, level.Wall())
            elif random.random() < 0.2:
                state.add_entity(xy, level.Box())
            elif random.random() <= 0.1:
                state.add_entity(xy, level.Potion(random.randint(0, colors.YELLOW_ID)))
            elif random.random() <= 0.1:
                direction = random.choice([(-1, 0), (1, 0), (0, 1), (0, -1), (0, 0)])
                state.add_entity(xy, level.Enemy(random.randint(0, colors.YELLOW_ID), direction))

    p_xy = random.randint(1, dims[0] - 2), random.randint(1, dims[1] - 2)
    for e in list(state.all_entities_at(p_xy)):
        state.remove_entity(p_xy, e)
    state.add_entity(p_xy, level.Player(colors.RED_ID))

    return state


def make_demo_from_json():
    return level.from_json(level.sample_blob)


class Game:

    def __init__(self, dims, fps=60):
        self.dims = dims
        self.fps = fps
        self.clock = None

    async def start(self):
        pygame.init()
        pygame.display.set_mode(self.dims)
        self.clock = pygame.time.Clock()

        dt = 0
        running = True

        sprites.load()
        sounds.load()
        colors.load(colorblind=configs.COLORBLIND_MODE)

        state = make_demo_state()
        renderer = rendering.AnimatedLevelRenderer(state, cell_size=48)

        while running:
            inputs.new_frame(pygame.time.get_ticks() / 1000.0)
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                elif e.type == pygame.KEYDOWN:
                    inputs.key_down(e.key)
                elif e.type == pygame.KEYUP:
                    inputs.key_up(e.key)
                elif e.type == pygame.MOUSEMOTION:
                    inputs.mouse_moved(e.pos)
                elif e.type == pygame.MOUSEBUTTONDOWN:
                    inputs.mouse_moved(e.pos)
                    inputs.mouse_button_down(e.button)

            if inputs.was_pressed(configs.RESET):
                state = make_demo_state2((13, 10))
                renderer.set_state(state, prev=None)
            elif inputs.was_pressed(configs.COLORBLIND_TOGGLE):
                configs.COLORBLIND_MODE = not configs.COLORBLIND_MODE
                colors.load(colorblind=configs.COLORBLIND_MODE)
                sprites.clear_cache()
            elif inputs.was_pressed(configs.ALL_MOVE_KEYS):
                if inputs.was_pressed(configs.MOVE_LEFT):
                    direction = (-1, 0)
                elif inputs.was_pressed(configs.MOVE_UP):
                    direction = (0, -1)
                elif inputs.was_pressed(configs.MOVE_RIGHT):
                    direction = (1, 0)
                elif inputs.was_pressed(configs.MOVE_DOWN):
                    direction = (0, 1)
                else:
                    direction = (0, 0)
                old_state = state
                state = old_state.get_next(direction)
                renderer.set_state(state, prev=old_state)
                print(f"step={state.step}:\t{state.what_was}")
                sounds.play("box_move")

            screen = pygame.display.get_surface()
            screen.fill("black")

            renderer.update()
            renderer.draw(screen)

            pygame.display.flip()
            pygame.display.set_caption(f"Color Quest [FPS={self.clock.get_fps():.1f}]")

            await asyncio.sleep(0)
            dt = self.clock.tick(self.fps)





