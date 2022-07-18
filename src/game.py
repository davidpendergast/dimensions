import pygame
import asyncio
import traceback

import configs
import src.inputs as inputs
import src.level as level
import src.colors as colors
import src.menus as menus
import src.rendering as rendering
import src.loader as loader
import src.userdata as userdata

import src.sprites as sprites
import src.sounds as sounds


class Game:

    def __init__(self, dims, fps=60):
        self.dims = dims
        self.fps = fps
        self.clock = None

        self.menu_manager = None

    def get_flags(self):
        if configs.WEB_MODE:
            return 0
        else:
            return pygame.RESIZABLE

    async def start(self):
        pygame.init()
        pygame.display.set_mode(self.dims, flags=self.get_flags())
        self.clock = pygame.time.Clock()

        dt = 0
        running = True

        colors.load(colorblind=configs.COLORBLIND_MODE)
        sprites.load()
        sounds.load()
        sounds.play_song(sounds.MAIN_SONG)
        loader.load_levels()

        userdata.initialize(configs.DATA_KEY, configs.get_save_mode(),
                            appname=configs.NAME_OF_GAME,
                            appauthor=configs.AUTHOR,
                            version=configs.VERSION)
        userdata.load_data_from_disk()

        self.menu_manager = menus.MenuManager(menus.MainMenu())

        while running:
            inputs.new_frame(pygame.time.get_ticks() / 1000.0)
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                elif e.type == pygame.KEYDOWN:
                    inputs.send_key_down(e.key)
                elif e.type == pygame.KEYUP:
                    inputs.send_key_up(e.key)
                elif e.type == pygame.MOUSEMOTION:
                    inputs.send_mouse_moved(e.pos)
                elif e.type == pygame.MOUSEBUTTONDOWN:
                    inputs.send_mouse_moved(e.pos)
                    inputs.send_mouse_button_down(e.button)

            if inputs.was_pressed(configs.COLORBLIND_TOGGLE):
                configs.COLORBLIND_MODE = not configs.COLORBLIND_MODE
                colors.load(colorblind=configs.COLORBLIND_MODE)
                sprites.clear_cache()

            if inputs.was_pressed(configs.MUSIC_TOGGLE):
                sounds.set_songs_muted(not configs.SONG_MUTED)

            if inputs.was_pressed(pygame.K_r) and configs.IS_DEV:
                shift_held = pygame.key.get_mods() & pygame.KMOD_SHIFT
                ctrl_held = pygame.key.get_mods() & pygame.KMOD_CTRL
                if shift_held and ctrl_held:
                    print("INFO: resetting save data ([Ctrl + Shift + R] was pressed)")
                    userdata.reset_data(hard=True)
                    sounds.play(sounds.LEVEL_QUIT)

            self.menu_manager.update(dt)

            screen = pygame.display.get_surface()
            self.menu_manager.draw(screen)

            pygame.display.flip()
            pygame.display.set_caption(f"Alien Knightmare [FPS={self.clock.get_fps():.1f}]")

            await asyncio.sleep(0)
            dt = self.clock.tick(self.fps) / 1000.0

            if inputs.was_quit_requested() and not configs.WEB_MODE:
                print("INFO: quit signal received; quitting")
                running = False





