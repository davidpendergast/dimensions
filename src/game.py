import pygame
import asyncio

import src.inputs as inputs


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
            screen.fill("purple")

            # TODO game

            pygame.display.flip()
            pygame.display.set_caption(f"Color Quest [FPS={self.clock.get_fps():.1f}]")

            await asyncio.sleep(0)
            dt = self.clock.tick(self.fps)





