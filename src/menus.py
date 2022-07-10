import typing

import pygame.font

import configs

import src.colors as colors
import src.utils as utils
import src.inputs as inputs
import src.sounds as sounds
import src.sprites as sprites

import src.level as level
import src.loader as loader
import src.rendering as rendering


class Menu:

    def __init__(self, bg_color=(0, 0, 0)):
        self.manager: 'MenuManager' = None
        self.elapsed_time = 0
        self.bg_color = bg_color

    def draw(self, screen):
        pass

    def fill_bg(self, screen):
        if self.bg_color is not None:
            screen.fill(self.bg_color)

    def update(self, dt):
        pass


class MenuManager:

    def __init__(self, cur_menu):
        self.cur_menu: Menu = cur_menu
        cur_menu.manager = self

        self.next_menu: typing.Optional[Menu] = None

    def get_menu(self) -> Menu:
        return self.cur_menu

    def set_menu(self, menu: Menu, immediately=False, cool_transition=False):
        if immediately:
            self.cur_menu = menu
            self.cur_menu.manager = self
            self.next_menu = None
        elif cool_transition:
            self.next_menu = TextTransitionMenu(None, self.cur_menu, menu, pause_time=0)
        else:
            self.next_menu = menu

    def update(self, dt):
        if self.next_menu is not None:
            self.cur_menu = self.next_menu
            self.cur_menu.manager = self
            self.next_menu = None

        self.cur_menu.update(dt)
        self.cur_menu.elapsed_time += dt

    def draw(self, screen):
        self.cur_menu.fill_bg(screen)
        self.cur_menu.draw(screen)


_CACHED_FONTS = {}  # (name, size) -> Font
_SIZE_MAPPING = {"S": 16, "M": 24, "L": 32, "H": 64}


def load_font(name, size) -> pygame.font.Font:
    if isinstance(size, str):
        size = _SIZE_MAPPING[size.upper()]
    key = name, size
    if key not in _CACHED_FONTS:
        filepath = utils.asset_path(f"assets/{name}.ttf")
        _CACHED_FONTS[key] = pygame.font.Font(filepath, size)
    return _CACHED_FONTS[key]


class TextRenderer:

    def __init__(self, text: str, size: typing.Union[int, str], color=(255, 255, 255), bg_color=None, font_name="alagard", y_kerning=0):
        self._text = text
        self._text_size = size
        self._text_color = color
        self._bg_color = bg_color
        self._text_font_name = font_name
        self._text_y_kerning = y_kerning

        # cached stuff
        self._text_font = load_font(font_name, size)
        self._cached_text_surfaces = None

        self._last_drawn_at_rect = None

    def _refresh(self, force=False):
        if force:
            self._cached_text_surfaces = None
            self._text_font = None

        if self._cached_text_surfaces is None or self._text_font is None:
            self._text_font = load_font(self._text_font_name, self._text_size)
            self._cached_text_surfaces = []
            for line in self._text.split("\n"):
                surf = self._text_font.render(line, False, self._text_color, self._bg_color)
                self._cached_text_surfaces.append(surf)

    def get_size(self):
        self._refresh()
        w, h = 0, 0
        for line_img in self._cached_text_surfaces:
            w = max(w, line_img.get_width())
            if h > 0:
                h += self._text_y_kerning
            h += line_img.get_height()
        return w, h

    def draw(self, dest_surf: pygame.Surface, xy, center_lines=False):
        self._refresh()
        x, y = xy
        w, h = self.get_size()
        for line_img in self._cached_text_surfaces:
            if center_lines:
                x_to_use = int(x + w / 2 - line_img.get_width() / 2)
            else:
                x_to_use = x
            dest_surf.blit(line_img, (x_to_use, y))
            y += line_img.get_height() + self._text_y_kerning

        self._last_drawn_at_rect = (x, xy[1], w, h)

    def draw_with_center_at(self, dest_surf, xy, center_lines=True):
        self._refresh()
        w, h = self.get_size()
        xy_to_use = xy[0] - w // 2, xy[1] - h // 2
        self.draw(dest_surf, xy_to_use, center_lines=center_lines)

    def get_last_drawn_rect(self):
        return self._last_drawn_at_rect

    def set_text(self, new_text):
        if new_text != self._text:
            self._text = new_text
            self._cached_text_surfaces = None

    def get_text(self):
        return self._text

    def set_color(self, color, bg_color="nochange"):
        if self._text_color != color or (bg_color != "nochange" and bg_color != self._bg_color):
            self._text_color = color
            self._bg_color = self._bg_color if bg_color == "nochange" else bg_color
            self._cached_text_surfaces = None
            self._text_font = None

    def set_size(self, size):
        if self._text_size != size:
            self._text_size = size
            self._cached_text_surfaces = None
            self._text_font = None


class MainMenu(Menu):

    def __init__(self):
        super().__init__()

        self._title_text = TextRenderer("Alien\nKnightmare", 'H', colors.get_color(colors.WHITE_ID))
        self._spacing = 16

        self._selected_opt = 0
        self._options = [
            TextRenderer("start", "L"),
            TextRenderer("levels", "L"),
        ]

        self.p_color_id = colors.rand_color_id()
        self.e_color_id = colors.rand_color_id()

    def _activate_option(self, idx=None):
        if idx is None:
            idx = self._selected_opt
        sounds.play(sounds.POTION_CONSUMED)
        if idx == 0:
            self.manager.set_menu(PlayingLevelMenu(loader.make_demo_state2((13, 9))), cool_transition=True)
        elif idx == 1:
            self.manager.set_menu(LevelSelectMenu(), cool_transition=True)

    def update(self, dt):
        old_selection = self._selected_opt
        if inputs.was_pressed(configs.MOVE_UP):
            self._selected_opt -= 1
        if inputs.was_pressed(configs.MOVE_DOWN):
            self._selected_opt += 1
        self._selected_opt %= len(self._options)

        # mouse stuff
        for idx, opt in enumerate(self._options):
            rect = opt.get_last_drawn_rect()
            if rect is not None:
                if inputs.did_mouse_move():
                    if utils.rect_contains(rect, inputs.get_mouse_pos()):
                        self._selected_opt = idx
                if inputs.did_click(btn=1, in_rect=rect):
                    self._activate_option(idx)

        if self._selected_opt != old_selection:
            self.p_color_id = colors.rand_color_id()
            self.e_color_id = colors.rand_color_id()
            sounds.play(sounds.PLAYER_MOVED)

        if inputs.was_pressed(configs.ENTER):
            self._activate_option()

        if inputs.was_pressed(configs.ESCAPE):
            inputs.send_quit_signal()

        for idx, opt in enumerate(self._options):
            if idx == self._selected_opt:
                opt.set_color(colors.get_color(colors.RED_ID))
            else:
                opt.set_color(colors.get_color(colors.WHITE_ID))

    def draw(self, screen: pygame.Surface):
        cx = screen.get_width() // 2
        title_cy = screen.get_height() // 3

        self._title_text.draw_with_center_at(screen, (cx, title_cy))
        options_y = title_cy + self._title_text.get_size()[1] // 2 + self._spacing * 2

        for opt in self._options:
            opt.draw(screen, (cx - opt.get_size()[0] // 2, options_y))
            options_y += opt.get_size()[1] + self._spacing

        player_spr = sprites.get_sprite(sprites.EntityID.BIG_PLAYER, 64 * 3, self.p_color_id)
        enemy_spr = sprites.get_sprite(sprites.EntityID.BIG_V_WALKER, 64 * 3, self.e_color_id, (-1, 0))

        screen.blit(player_spr, (screen.get_width() / 4 - player_spr.get_width() / 2, title_cy + self._title_text.get_size()[1]))
        screen.blit(enemy_spr, (3 * screen.get_width() / 4 - enemy_spr.get_width() / 2, title_cy + self._title_text.get_size()[1]))


class IntroCutsceneMenu(Menu):

    def __init__(self):
        super().__init__()

    def update(self, dt):
        self.manager.set_menu(PlayingLevelMenu(loader.make_demo_state2((13, 9))))


class LevelSelectMenu(Menu):

    def __init__(self, selected_id=None):
        super().__init__()


class TextTransitionMenu(Menu):

    def __init__(self, text_renderer, from_menu, to_menu, pause_time=1, fadeout_time=0.25, fadein_time=0.25,
                 bg_color=(0, 0, 0), center_lines=True):
        super().__init__()
        self.text = text_renderer
        self.center_lines = center_lines

        self.from_menu = from_menu
        self.to_menu = to_menu

        self.pause_time = pause_time
        self.fadeout_time = fadeout_time
        self.fadein_time = fadein_time

        self.bg_color = None  # parent stuff
        self.my_bg_color = bg_color

        self.overlay = None

    def update(self, dt):
        if self.elapsed_time >= self.fadein_time + self.pause_time + self.fadeout_time:
            self.manager.set_menu(self.to_menu, cool_transition=False)

    def draw(self, screen):
        t = self.elapsed_time
        if t <= self.fadein_time:
            opacity = t / self.fadein_time
            self.from_menu.fill_bg(screen)
            self.from_menu.draw(screen)
        elif t <= self.fadein_time + self.pause_time:
            opacity = 1.0
        else:
            opacity = max(0.0, 1 - (t - self.fadein_time - self.pause_time) / self.fadeout_time)
            self.to_menu.fill_bg(screen)
            self.to_menu.draw(screen)

        if self.overlay is None or self.overlay.get_size() != screen.get_size():
            self.overlay = pygame.Surface(screen.get_size())
            self.overlay.fill(self.my_bg_color)
            if self.text is not None:
                cxy = self.overlay.get_rect().center
                self.text.draw_with_center_at(self.overlay, cxy, center_lines=self.center_lines)

        self.overlay.set_alpha(int(255 * opacity))
        print(f"INFO: opacity={int(255 * opacity)}")
        screen.blit(self.overlay, (0, 0))


class PlayingLevelMenu(Menu):

    def __init__(self, initial_state):
        super().__init__()
        self.initial_state = initial_state
        self.state = self.initial_state.copy()
        self.renderer = rendering.AnimatedLevelRenderer(self.state, cell_size=48)

    def update(self, dt):
        if inputs.was_pressed(configs.RESET):
            if inputs.is_held(pygame.K_LSHIFT):  # TODO debug only
                self.initial_state = loader.make_demo_state2((13, 9))

            self.state = self.initial_state.copy()
            self.renderer.set_state(self.state, prev=None)
            sounds.play(sounds.RESET_LEVEL)
        elif inputs.was_pressed(configs.UNDO):
            prev = self.state.get_prev()
            if prev is not None:
                old_cur = self.state
                self.state = prev.copy()  # probably don't *need* to copy here, but eh
                self.renderer.set_state(self.state, prev=old_cur)
            sounds.play(sounds.UNDO_LEVEL)
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
            old_state = self.state
            self.state = old_state.get_next(direction)
            self.renderer.set_state(self.state, prev=old_state)
            self.state.what_was.play_sounds()
            print(f"step={self.state.step}:\t{self.state.what_was}")

        if inputs.was_pressed(configs.ESCAPE):
            self.manager.set_menu(MainMenu())
            # self.manager.set_menu(LevelSelectMenu(selected_id=self.state.name))

    def draw(self, screen):
        self.renderer.get_offset_for_centering(screen, and_apply=True)
        self.renderer.update()
        self.renderer.draw(screen)

