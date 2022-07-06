import pygame
import asyncio

import src.inputs as inputs
import src.level as level
import src.sprites as sprites
import src.colors as colors


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

        state = level.State(0, 0)
        state.add_entity((4, 4), level.Entity(sprites.EntityID.PLAYER, 1))
        state.add_entity((5, 2), level.Entity(sprites.EntityID.WALL, 0))
        state.add_entity((5, 3), level.Entity(sprites.EntityID.WALL, 0))
        state.add_entity((5, 4), level.Entity(sprites.EntityID.WALL, 0))
        state.add_entity((6, 4), level.Entity(sprites.EntityID.WALL, 0))
        state.add_entity((7, 4), level.Entity(sprites.EntityID.WALL, 0))
        state.add_entity((6, 5), level.Entity(sprites.EntityID.H_WALKER, colors.GREEN_ID, (-1, 0)))
        state.add_entity((2, 5), level.Entity(sprites.EntityID.BOX, colors.BROWN_ID))
        state.add_entity((3, 6), level.Entity(sprites.EntityID.BOX, colors.BROWN_ID))
        state.add_entity((5, 7), level.Entity(sprites.EntityID.BOX, colors.BROWN_ID))
        state.add_entity((8, 5), level.Entity(sprites.EntityID.POTION, colors.PINK_ID))

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

            screen = pygame.display.get_surface()
            screen.fill("black")

            state.render_level(screen, (0, 0), cellsize=48)

            # TODO game

            pygame.display.flip()
            pygame.display.set_caption(f"Color Quest [FPS={self.clock.get_fps():.1f}]")

            await asyncio.sleep(0)
            dt = self.clock.tick(self.fps)





