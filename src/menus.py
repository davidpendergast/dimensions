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
import src.textrendering as tr


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

    def set_menu(self, menu: Menu, immediately=False,
                 transition: typing.Union[str, bool, typing.Tuple, tr.TextRenderer] = False):
        if immediately:
            self.cur_menu = menu
            self.cur_menu.manager = self
            self.next_menu = None
        elif transition or transition == "":
            trans_text = None
            if isinstance(transition, str):
                trans_text = tr.TextRenderer(transition, "L", colors.get_white(), alignment=0, y_kerning=8)
            elif isinstance(transition, tuple):
                trans_text = tr.TextRenderer(transition[0], "L", alignment=0, y_kerning=8)
                if len(transition) > 1 and transition[1] is not None:
                    trans_text.set_color(colors.get_color(transition[1]))
                if len(transition) > 2 and transition[2] is not None:
                    trans_text.set_size(transition[2])
            elif isinstance(transition, tr.TextRenderer):
                trans_text = transition

            self.next_menu = TextTransitionMenu(trans_text, self.cur_menu, menu,
                                                pause_time=0.666 if trans_text is not None else 0)
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


class MainMenu(Menu):

    def __init__(self):
        super().__init__()

        self._title_text = tr.TextRenderer("Alien\nKnightmare", 'H', colors.get_white(), alignment=0)
        self._spacing = 16

        self._selected_opt = 0
        self._options = [
            tr.TextRenderer("start", "L", alignment=0),
            tr.TextRenderer("levels", "L", alignment=0),
        ]

        self.p_color_id = colors.rand_color_id()
        self.e_color_id = colors.rand_color_id()

    def _activate_option(self, idx=None):
        if idx is None:
            idx = self._selected_opt
        sounds.play(sounds.POTION_CONSUMED)
        if idx == 0:
            self.manager.set_menu(PlayingLevelMenu(loader.get_level_by_idx(0)), transition=True)
        elif idx == 1:
            self.manager.set_menu(LevelSelectMenu(), transition=True)

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
                opt.set_color(colors.get_white())

    def draw(self, screen: pygame.Surface):
        cx = screen.get_width() // 2
        title_cy = screen.get_height() // 4

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
        self.manager.set_menu(PlayingLevelMenu(loader.get_level_by_idx(0)))


class LevelSelectMenu(Menu):

    def __init__(self, selected_name=None, row_size=8):
        super().__init__()
        self.levels = [l for l in loader.all_levels()]
        self.completed = set(l.name for l in self.levels if loader.is_completed(l.name))
        self.max_completed_idx = -1 if len(self.completed) == 0 else max(loader.idx_of(name) for name in self.completed)
        self.row_size = row_size

        self.selected_idx = loader.idx_of(selected_name) if selected_name is not None else -1
        if self.selected_idx == -1:
            self.selected_idx = 0

        self.title_text = tr.TextRenderer("Level Select", size="H", color=colors.get_white(), alignment=0)
        if len(self.completed) < len(self.levels):
            self.info_text = tr.TextRenderer(f"Completed: {len(self.completed)}/{len(self.levels)}", size="M", alignment=0)
        else:
            total_steps = sum(loader.is_completed(l.name) for l in self.completed)
            self.info_text = tr.TextRenderer(f"All Complete! Total Steps: {total_steps}", size="M", alignment=0)

        self.selected_level_text = tr.TextRenderer("", size="M", color=colors.get_white(), alignment=0)
        self._update_selected_level_text()

        self.grid_rect = (0, 0, 10, 10)  # bwah
        self.cell_rects = []
        self.cell_text = []

    def _update_selected_level_text(self):
        sel_name = self.get_selected().name
        if sel_name in self.completed:
            status = f"Completed in {loader.is_completed(sel_name)} Steps"
        elif self.is_unlocked(sel_name):
            status = "Incomplete"
        else:
            status = "Locked"
        self.selected_level_text.set_text(f"{sel_name}: {status}")

    def get_selected(self) -> level.State:
        return self.levels[self.selected_idx]

    def is_unlocked(self, name):
        name_idx = loader.idx_of(name)
        return name_idx <= self.max_completed_idx + 1

    def draw(self, screen):
        cx = screen.get_width() // 2
        y = screen.get_height() // 4
        spacing = 16
        self.title_text.draw_with_center_at(screen, (cx, y))
        y += self.title_text.get_size()[1] // 2

        y += self.info_text.get_size()[1] // 2 + spacing
        self.info_text.draw_with_center_at(screen, (cx, y))
        y += self.info_text.get_size()[1] // 2 + spacing

        grid_rect_top = y

        sel_level_xy = (cx, screen.get_height() - spacing - self.selected_level_text.get_size()[1] // 2)
        self.selected_level_text.draw_with_center_at(screen, sel_level_xy)

        grid_rect_bottom = self.selected_level_text.get_last_drawn_rect()[1] - spacing
        self.grid_rect = (spacing, grid_rect_top, screen.get_width() - spacing * 2, grid_rect_bottom - grid_rect_top)
        grid_cell_size = (self.grid_rect[2] / self.row_size, spacing * 3)
        self.cell_rects.clear()

        for grid_idx in range(len(self.levels)):
            l = self.levels[grid_idx]
            grid_xy = (grid_idx % self.row_size, grid_idx // self.row_size)

            line_width = 2
            r = (int(self.grid_rect[0] + grid_xy[0] * grid_cell_size[0]),
                 int(self.grid_rect[1] + grid_xy[1] * grid_cell_size[1]),
                 int(grid_cell_size[0]), int(grid_cell_size[1]))
            r = utils.expand_rect(r, -2)
            self.cell_rects.append(r)

            if grid_idx == self.selected_idx:
                c = colors.get_color(colors.RED_ID)
            elif l.name in self.completed:
                c = colors.get_color(colors.GREEN_ID)
            elif self.is_unlocked(l.name):
                c = colors.get_white()
            else:
                c = colors.get_gray()

            if grid_idx >= len(self.cell_text):
                text = tr.TextRenderer("", size="M", alignment=0)
                self.cell_text.append(text)
            else:
                text = self.cell_text[grid_idx]
            text.set_text(f"{grid_idx + 1}")
            text.set_color(c)

            text.draw_with_center_at(screen, utils.rect_center(r))
            pygame.draw.rect(screen, c, r, line_width)

    def try_to_activate_level(self, level_idx) -> bool:
        if 0 <= level_idx < len(self.levels):
            l = self.levels[level_idx]
            if self.is_unlocked(l.name):
                sounds.play(sounds.LEVEL_START)
                self.manager.set_menu(PlayingLevelMenu(l), transition=True)
                return True

        sounds.play(sounds.ERROR)
        return False

    def update(self, dt):
        if inputs.was_pressed(configs.ESCAPE):
            self.manager.set_menu(MainMenu(), transition=True)
            sounds.play(sounds.LEVEL_QUIT)

        if inputs.was_pressed(configs.ENTER):
            self.try_to_activate_level(self.selected_idx)

        dx, dy = 0, 0
        if inputs.was_pressed(configs.MOVE_UP):
            dy -= 1
        if inputs.was_pressed(configs.MOVE_DOWN):
            dy += 1
        if inputs.was_pressed(configs.MOVE_LEFT):
            dx -= 1
        if inputs.was_pressed(configs.MOVE_RIGHT):
            dx += 1

        if dx != 0 or dy != 0:
            self.selected_idx += dx
            self.selected_idx += self.row_size * dy
            sounds.play(sounds.PLAYER_MOVED)

        if inputs.did_click() or inputs.did_mouse_move():
            pos = inputs.get_mouse_pos()
            for idx, r in enumerate(self.cell_rects):
                if inputs.did_click(in_rect=r):
                    self.try_to_activate_level(idx)
                elif utils.rect_contains(r, pos) and idx != self.selected_idx:
                    self.selected_idx = idx
                    sounds.play(sounds.PLAYER_MOVED)

        self.selected_idx %= len(self.levels)
        self._update_selected_level_text()


class WinMenu(Menu):

    def __init__(self):
        super().__init__()

    def update(self, dt):
        self.manager.set_menu(MainMenu())


class TextTransitionMenu(Menu):

    def __init__(self, text_renderer, from_menu, to_menu, pause_time=1,
                 fadeout_time=0.25, fadein_time=0.25, bg_color=(0, 0, 0)):
        super().__init__()
        self.text = text_renderer

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
            self.manager.set_menu(self.to_menu, transition=False)

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
                self.text.draw_with_center_at(self.overlay, cxy)

        self.overlay.set_alpha(int(255 * opacity))
        screen.blit(self.overlay, (0, 0))


class PlayingLevelMenu(Menu):

    def __init__(self, initial_state):
        super().__init__()
        self.initial_state = initial_state
        self.state = self.initial_state.copy()
        self.renderer = rendering.AnimatedLevelRenderer(self.state, cell_size=48)

    def update(self, dt):
        if inputs.was_pressed(configs.RESET):
            if configs.IS_DEBUG and inputs.is_held(pygame.K_LSHIFT):  # TODO debug only
                self.initial_state = loader.make_demo_state2()

            self.state = self.initial_state.copy()
            self.renderer.set_state(self.state, prev=None)
            sounds.play(sounds.RESET_LEVEL)
        elif configs.IS_DEBUG and inputs.was_pressed(pygame.K_k):
            self.state = self.state.get_next((0, 0))
            for e, xy in list(self.state.all_entities_with_type(sprites.EntityID.all_enemies())):
                self.state.remove_entity(xy, e)
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
            self.manager.set_menu(LevelSelectMenu(selected_name=self.state.name), transition=True)
            sounds.play(sounds.LEVEL_QUIT)

        elif self.state.step > 0 and self.state.is_success():
            loader.set_completed(self.state.name, self.state.step)
            idx = loader.idx_of(self.state.name)
            if idx == -1:
                # some kind of bad state, idk
                self.manager.set_menu(MainMenu(), transition=True)
            else:
                next_idx = idx + 1
                if next_idx >= loader.num_levels():
                    self.manager.set_menu(MainMenu(), transition="You Win!")
                    sounds.play(sounds.GAME_WON)
                else:
                    next_level_state = loader.get_level_by_idx(next_idx)
                    p_color = self.state.get_player_color()
                    text = f"Floor Cleared!\nSteps: {self.state.step}"
                    self.manager.set_menu(PlayingLevelMenu(next_level_state), transition=(text, p_color, "L"))
                    sounds.play(sounds.LEVEL_COMPLETED)

    def draw(self, screen):
        self.renderer.get_offset_for_centering(screen, and_apply=True)
        self.renderer.update()
        self.renderer.draw(screen)

