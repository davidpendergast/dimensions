import os.path
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
            tr.TextRenderer("controls", "L", alignment=0),
            tr.TextRenderer("credits", "L", alignment=0)
        ]

        self.p_color_id = colors.rand_color_id()
        self.e_color_id = colors.rand_color_id()

    def _activate_option(self, idx=None):
        if idx is None:
            idx = self._selected_opt
        sounds.play(sounds.POTION_CONSUMED)
        if idx == 0:
            playing_menu = PlayingLevelMenu(loader.get_level_by_idx(0))
            lore_txt = get_lore_text(0)
            if lore_txt is not None:
                self.manager.set_menu(LoreMenu(lore_txt, playing_menu), transition=True)
            else:
                self.manager.set_menu(playing_menu, transition=True)
        elif idx == 1:
            self.manager.set_menu(LevelSelectMenu(), transition=True)
        elif idx == 2:
            self.manager.set_menu(InstructionsMenu(self), transition=True)
        elif idx == 3:
            self.manager.set_menu(CreditsMenu(self), transition=True)

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


class CutSceneMenu(Menu):

    def __init__(self, pages: typing.List[tr.TextRenderer], next_menu: Menu, idx=0):
        super().__init__()
        self.pages = pages
        self.next = next_menu
        self.cur_idx = idx

    def update(self, dt):
        next_idx = self.cur_idx
        if inputs.was_pressed(configs.ENTER + configs.RESET) or inputs.did_click():
            next_idx += 1
        elif inputs.was_pressed(configs.ESCAPE):
            next_idx = len(self.pages)

        if next_idx >= len(self.pages):
            self.manager.set_menu(self.next, transition=True)
        elif next_idx != self.cur_idx:
            sounds.play(sounds.PLAYER_MOVED)
            self.manager.set_menu(CutSceneMenu(self.pages, self.next, idx=next_idx), transition=True)

    def draw(self, screen):
        if 0 <= self.cur_idx < len(self.pages):
            page = self.pages[self.cur_idx]
            if page is not None:
                cxy = screen.get_width() // 2, screen.get_height() // 2
                page.draw_with_center_at(screen, cxy)


class InstructionsMenu(CutSceneMenu):

    def __init__(self, next_menu):
        pages = [tr.TextRenderer("Defend the castle from the aliens!\n\n"
                                 "[WASD] or arrow keys to Move\n"
                                 "[R] to Reset Level\n"
                                 "[Z] to Undo\n"
                                 "[M] to Mute music\n\n"
                                 "Walk into walls to skip turn", "M", alignment=0, y_kerning=2)]
        super().__init__(pages, next_menu)


class CreditsMenu(CutSceneMenu):

    def __init__(self, next_menu):
        pages = [tr.TextRenderer("Art, Code, and Concept by Ghast\nghastly.itch.io\n\n"
                                 "Music: fakemusicgenerator.com / cgMusic\n"
                                 "Font: Alagard by Hewett Tsoi\n"
                                 "Sound effects: sfxr.me\n\n"
                                 "Story: OpenAI Playground\n"
                                 "(from many prompts,\nedited & arranged by me)\n\n"
                                 "Built using python, pygame & pygame-wasm", "M", alignment=0, y_kerning=2)]

        super().__init__(pages, next_menu)


_LORE_TEXT = [
    "The aliens came in the night, a colorful horde intent\n" 
    "on conquering the castle. But the knight was ready.\n" 
    "He had boxes, lots of boxes.",

    "The aliens were baffled by the knight's defenses.\n"
    "They couldn't get past the boxes. So they resorted\n"
    "to throwing themselves at the knight, hoping to\n"
    "overwhelm him. But the knight was ready.",

    "The brave knight had been defending his castle\n"
    "from interdimensional aliens for years. He had\n"
    "seen them come in all shapes and sizes, but he\n"
    "had never seen anything like the creatures that\n"
    "were attacking his castle now.",

    "They were huge, with tentacles that seemed to\n"
    "be made of metal. They were also incredibly fast,\n"
    "and it was all the knight could do to keep up\n"
    "with them.",

    "The knight drank the first potion and his armor\n"
    "turned blue. He used his new camouflage to sneak up\n"
    "on the aliens and ambush them. He immediately felt\n"
    "more confident and brave. ",

    "The aliens had been attacking earth for weeks,\n"
    "and it seemed like they were never going to stop.\n"
    "The knight had been fighting them off as best as\n"
    "he could, but he was getting tired.",

    ("The knight was getting tired, but he knew he had\n"
    "to keep going. He had to find a way to defeat this\n"
    "alien. Suddenly, he had an idea. He feinted to the\n"
    "left, and when the alien reacted, he quickly dodged\n"
    "to the right.",

    "The alien was off balance for a moment, and the\n"
    "knight took his opportunity. He ran up to the\n"
    "alien and, using all his strength, knocked it to\n"
    "the ground."),

    "Just when it seemed like the knight was done for,\n"
    "he remembered his training. He focused his energy\n"
    "and willed himself to phase through the wall behind\n"
    "him. The alien crashed into the wall, dazed from the\n"
    "impact.",

    "The knight had been fighting aliens for years,\n"
    "and it seemed like they were getting more and\n"
    "more clever. They had started using boxes and\n"
    "potions to try to defeat him, but he was always\n"
    "one step ahead.",

    "He had developed a keen sense for when they were\n"
    "going to attack and was able to counter their\n"
    "every move. But the aliens were getting stronger,\n"
    "and the knight was running out of ideas.",

    "He knew that he needed to find a way to defeat the\n"
    "aliens once and for all, or the world would be lost.\n\n"
    "The knight rode into the basin, prepared for battle.\n"
    "He had been warned about the two blue aliens that\n"
    "resided there, and was ready to take them on.",

    "The knight spent days locked in his laboratory,\n"
    "trying to come up with a new plan.\n\n"
    "Finally, he had a breakthrough. He created a new\n"
    "box, one that was so powerful it could kill an\n"
    "alien by crushing it against a wall.",

    ("As he rounded a corner, he saw a group of aliens\n"
    "clustered together. They were laughing and joking,\n"
    "and they didn't see the knight coming. He crept up\n"
    "behind them, and then he attacked.",

    "He threw boxes of colorful powder at them, and they\n"
    "screamed as the powder hit them. He followed up with\n"
    "bottles of potion, and the aliens were soon defeated."),

    "He decided to crush them with boxes. It was a simple\n"
    "plan, but it worked. The aliens didn't stand a chance\n"
    "against the knight's might. They were no match for\n"
    "his strength and his determination.\n\n"
    "The knight crushed them all, one by one, until they\n"
    "were nothing but colored smears on the floor.",

    "Finally, he arrived at the castle's dungeon, ready\n"
    "to vanquish the evil that lurked within. But to his\n"
    "surprise, the dungeon was swarming with\n"
    "translucent aliens.\n\n"
    "The knight had never faced such creatures before\n"
    "and was quickly overwhelmed. As the aliens closed\n"
    "in around him, the knight feared that his quest\n"
    "had come to an end.",

    "The aliens came at him in a huge swarm. They were\n"
    "unlike anything he had ever seen before. He was\n"
    "outnumbered and outmatched, but he refused to\n"
    "give up.\n\n"
    "He kept fighting, even when he was injured. He was\n"
    "determined to protect his people and defeat the\n"
    "aliens."
]

GAME_OVER_LORE = (
    "The aliens were no match for the knight's skill\n"
    "and strength, and soon they were retreating back\n"
    "to their ship.\n\n"
    "The knight triumphantly rode back to the castle,\n"
    "where the people cheered for him and hailed him\n"
    "as a hero.")


SNEK_LORE = (
    "The knight was on his horse, trotting through\n"
    "the forest when he saw a large yellow python\n"
    "blocking his path. The knight stopped and\n"
    "asked the python what it wanted.",

    "The python told the knight that it wanted to\n"
    "play a game. If the knight could answer its\n"
    "riddle, the python would let him pass.\n"
    "If the knight couldn't answer the riddle,\n"
    "the python would eat him. ",

    "The knight agreed to the game and the python\n"
    "asked its riddle.\n"
    
    "\"What will this expression evaluate to?\"\n\n"
    "{True: 'yes', 1: 'no', 1.0: 'maybe'}\n\n",

    "The knight did some calculations in his head\n"
    "for a moment and then answered. The python\n"
    "was pleased with the answer and moved aside,\n"
    "letting the knight pass."
)


def get_lore_text(level_idx):
    if 0 <= level_idx < len(_LORE_TEXT):
        return _LORE_TEXT[level_idx]
    else:
        return None


class LoreMenu(CutSceneMenu):

    def __init__(self, text, next_menu):
        if not isinstance(text, tuple):
            text = (text, )
        color = colors.get_color(colors.rand_color_id(include_white=True))
        pages = [tr.TextRenderer(t, size="M", color=color, y_kerning=4) for t in text]
        super().__init__(pages, next_menu)


class YouWinMenu(CutSceneMenu):

    def __init__(self, steps, next_menu):
        page_texts = [
            f"You Win!\nTotal Steps: {steps}",
            "Made by Ghast\n\n@Ghast_NEOH\nghastly.itch.io",
            "Entry to:\n\nPygame Community\nSummer Jam 2022\n\n(8-day duration)",
            "Thanks for playing :)"
        ]
        pages = [tr.TextRenderer(t, size="L", color=colors.get_color(colors.rand_color_id()),
                                 y_kerning=4, alignment=0) for t in page_texts]
        super().__init__(pages, next_menu)


class LevelSelectMenu(Menu):

    def __init__(self, selected_name=None, row_size=8):
        super().__init__()
        self.levels = [l for l in loader.all_levels()]
        self.completed_names = set(l.name for l in self.levels if loader.is_completed(l.name))
        self.max_completed_idx = -1 if len(self.completed_names) == 0 else max(loader.idx_of(name) for name in self.completed_names)
        self.row_size = row_size

        self.selected_idx = loader.idx_of(selected_name) if selected_name is not None else -1
        if self.selected_idx == -1:
            self.selected_idx = 0

        self.title_text = tr.TextRenderer("Level Select", size="H", color=colors.get_white(), alignment=0)
        if len(self.completed_names) < len(self.levels):
            self.info_text = tr.TextRenderer(f"Completed: {len(self.completed_names)}/{len(self.levels)}", size="M", alignment=0)
        else:
            total_steps = sum(loader.is_completed(n) for n in self.completed_names)
            self.info_text = tr.TextRenderer(f"All Complete! Total Steps: {total_steps}", size="M", alignment=0)

        self.selected_level_text = tr.TextRenderer("", size="M", color=colors.get_white(), alignment=0)
        self._update_selected_level_text()

        self.grid_rect = (0, 0, 10, 10)  # bwah
        self.cell_rects = []
        self.cell_text = []

    def _update_selected_level_text(self):
        sel_name = self.get_selected().name
        if sel_name in self.completed_names:
            status = f"Completed in {loader.is_completed(sel_name)} Steps"
        elif self.is_unlocked(sel_name):
            status = "Incomplete"
        else:
            status = "Locked"
        self.selected_level_text.set_text(f"{sel_name}: {status}")

    def get_selected(self) -> level.State:
        return self.levels[self.selected_idx]

    def is_unlocked(self, name):
        if configs.IS_DEBUG and configs.DEBUG_ALL_UNLOCKED:
            return True
        else:
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
            elif l.name in self.completed_names:
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
                playing_menu = PlayingLevelMenu(l)
                lore_text = get_lore_text(level_idx)
                if not loader.is_completed(l.name) and lore_text is not None:
                    self.manager.set_menu(LoreMenu(lore_text, playing_menu), transition=True)
                else:
                    self.manager.set_menu(playing_menu, transition=True)

                sounds.play(sounds.LEVEL_START)
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

    def do_reset(self, silent=False):
        self.state = self.initial_state.copy()
        self.renderer.set_state(self.state, prev=None)
        if not silent:
            sounds.play(sounds.LEVEL_RESET)

    def update(self, dt):
        if inputs.was_pressed(configs.RESET):
            if configs.IS_DEBUG and inputs.is_held(pygame.K_LSHIFT):
                self.initial_state = loader.make_demo_state2()
            self.do_reset()
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
            elif inputs.was_pressed(configs.MOVE_DOWN) and (not configs.IS_DEBUG or not inputs.is_held(pygame.K_LCTRL)):
                direction = (0, 1)
            else:
                direction = (0, 0)
            old_state = self.state
            self.state = old_state.get_next(direction)
            self.renderer.set_state(self.state, prev=old_state)
            self.state.what_was.play_sounds()
            print(f"step={self.state.step}:\t{self.state.what_was}")

        # level editing stuff
        if configs.IS_DEBUG:
            mouse_xy = self.renderer.get_grid_cell_at(inputs.get_mouse_pos())
            if inputs.was_pressed(pygame.K_s) and inputs.is_held(pygame.K_LCTRL):
                self.do_reset(silent=True)

                path_to_use = f"saved/{self.initial_state.name}.json"
                overwrite = False
                if (configs.DEBUG_OVERWRITE_WHILE_SAVING
                        and not inputs.is_held(pygame.K_LSHIFT)
                        and self.initial_state.original_filepath is not None
                        and os.path.exists(self.initial_state.original_filepath)):
                    path_to_use = self.initial_state.original_filepath
                    overwrite = True

                self.initial_state.save_to_json(path_to_use, allow_overwrite=overwrite)

            if mouse_xy is not None and inputs.was_pressed((pygame.K_DELETE, pygame.K_e)):
                self.initial_state.remove_all_entities_at(mouse_xy)
                self.do_reset(silent=True)
            if mouse_xy is not None and inputs.was_pressed(pygame.K_q):
                self.initial_state.remove_all_entities_at(mouse_xy)
                self.initial_state.add_entity(mouse_xy, level.Wall(), ignore_bounds=True)
                self.do_reset(silent=True)
            if mouse_xy is not None and inputs.was_pressed(pygame.K_p):
                self.initial_state.add_entity(mouse_xy, level.Player(colors.RED_ID), ignore_bounds=True)
                self.do_reset(silent=True)
            if mouse_xy is not None and inputs.was_pressed(pygame.K_b):
                self.initial_state.remove_all_entities_at(mouse_xy)
                self.initial_state.add_entity(mouse_xy, level.Box(), ignore_bounds=True)
                self.do_reset(silent=True)
            if mouse_xy is not None and inputs.was_pressed(pygame.K_j):
                self.initial_state.add_entity(mouse_xy, level.Enemy(colors.BLUE_ID, (-1, 0)), ignore_bounds=True)
                self.do_reset(silent=True)
            if mouse_xy is not None and inputs.was_pressed(pygame.K_k):
                self.initial_state.add_entity(mouse_xy, level.Enemy(colors.BLUE_ID, (0, 1)), ignore_bounds=True)
                self.do_reset(silent=True)
            if mouse_xy is not None and inputs.was_pressed(pygame.K_l):
                self.initial_state.add_entity(mouse_xy, level.Enemy(colors.BLUE_ID, (1, 0)), ignore_bounds=True)
                self.do_reset(silent=True)
            if mouse_xy is not None and inputs.was_pressed(pygame.K_i):
                self.initial_state.add_entity(mouse_xy, level.Enemy(colors.BLUE_ID, (0, -1)), ignore_bounds=True)
                self.do_reset(silent=True)
            if mouse_xy is not None and inputs.was_pressed(pygame.K_o):
                self.initial_state.add_entity(mouse_xy, level.Enemy(colors.BLUE_ID, (0, 0)), ignore_bounds=True)
                self.do_reset(silent=True)
            if mouse_xy is not None and inputs.was_pressed(pygame.K_y):
                self.initial_state.add_entity(mouse_xy, level.Potion(colors.GREEN_ID), ignore_bounds=True)
                self.do_reset(silent=True)
            for k in range(pygame.K_1, pygame.K_7 + 1):
                if mouse_xy is not None and inputs.was_pressed(k):
                    for ent in self.initial_state.all_entities_at(mouse_xy):
                        ent.color_id = k - pygame.K_1
                    self.do_reset(silent=True)

            if inputs.was_pressed(pygame.K_EQUALS):  # win button
                self.state = self.state.get_next((0, 0))
                for e, xy in list(self.state.all_entities_with_type(sprites.EntityID.all_enemies())):
                    self.state.remove_entity(xy, e)

        if inputs.was_pressed(configs.ESCAPE):
            self.manager.set_menu(LevelSelectMenu(selected_name=self.state.name), transition=True)
            sounds.play(sounds.LEVEL_QUIT)

        elif self.state.step > 0 and self.state.is_success():
            loader.set_completed(self.state.name, self.state.step)
            idx = loader.idx_of(self.state.name)

            if configs.IS_DEBUG and configs.DEBUG_NO_CONTINUE:
                print("INFO: Resetting because we're in dev")
                self.do_reset()
            elif idx == -1:
                # some kind of bad state, idk
                self.manager.set_menu(MainMenu(), transition=True)
            else:
                p_color = self.state.get_player_color()
                lvl_cleared_text = (f"Floor Cleared!\nSteps: {self.state.step}", p_color, "L")

                next_idx = idx + 1
                if next_idx >= loader.num_levels():
                    total_steps = loader.get_total_steps()
                    win_menu = YouWinMenu(total_steps, next_menu=MainMenu())
                    self.manager.set_menu(LoreMenu(GAME_OVER_LORE, win_menu), transition=lvl_cleared_text)
                    sounds.play(sounds.GAME_WON)
                else:
                    next_level_state = loader.get_level_by_idx(next_idx)
                    next_menu = PlayingLevelMenu(next_level_state)

                    lore_text = get_lore_text(next_idx)
                    if lore_text is not None:
                        next_menu = LoreMenu(lore_text, next_menu)

                    self.manager.set_menu(next_menu, transition=lvl_cleared_text)
                    sounds.play(sounds.LEVEL_COMPLETED)

    def draw(self, screen):
        self.renderer.get_offset_for_centering(screen, and_apply=True)
        self.renderer.update()
        self.renderer.draw(screen)

