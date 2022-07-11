import typing
import random
import math

import pygame

import src.level as level
import src.inputs as inputs
import src.utils as utils
import src.sprites as sprites
import src.colors as colors
import src.textrendering as tr


class LevelRenderer:

    def __init__(self, state, cell_size=32):
        self.cur_state: level.State = state
        self.prev_state: typing.Optional[level.State] = None
        self.prev_state_time = 0

        self.centered = True
        self.xy_offset = (0, 0)
        self.cell_size = cell_size

        self.you_died_text = None
        self.r_to_restart_text = None
        self.success_text = None

        self.goal_text = None
        self.dimension_text = None
        self.in_progress_text = None
        self.controls_text = None

    def set_state(self, state, prev='current'):
        if prev == 'current':
            self.prev_state = self.cur_state
        elif state == prev:
            return
        else:
            self.prev_state = prev
        self.cur_state = state
        self.prev_state_time = inputs.get_time()

    def set_offset(self, offs_xy):
        if offs_xy is not None:
            self.xy_offset = offs_xy

    def get_offset_for_centering(self, screen: pygame.Surface, state=None, and_apply=True):
        play_rect, *_ = self.get_play_area_and_info_rects_and_inset(screen)
        state = state or self.cur_state
        if state is not None:
            rect = utils.scale(state.get_area(), self.cell_size)
            screen_center = utils.rect_center(play_rect)
            world_center = utils.rect_center(rect)
            res = utils.sub(screen_center, world_center)
            if and_apply:
                self.set_offset(res)
            return res
        else:
            return None

    def update(self):
        pass

    def all_sorted_entities_to_render(self):
        if self.cur_state is not None:
            for xy in self.cur_state.level:
                for ent in self.cur_state.level[xy]:
                    yield ent, xy

    def draw_entity_at(self, ent, surf, xy):
        if isinstance(ent, level.Entity):
            ent_sprite = ent.get_sprite(self.cell_size)
        elif isinstance(ent, pygame.Surface):
            ent_sprite = ent
        else:
            raise ValueError(f"cannot draw {ent}")

        ent_xy = (round(self.xy_offset[0] + self.cell_size * xy[0]),
                  round(self.xy_offset[1] + self.cell_size * xy[1]))
        surf.blit(ent_sprite, ent_xy)

    def get_grid_cell_at(self, screen_xy):
        screen_xy_wo_offset = utils.sub(screen_xy, self.xy_offset)
        grid_xy = utils.scale(screen_xy_wo_offset, 1 / self.cell_size)
        return int(grid_xy[0]), int(grid_xy[1])

    def draw(self, surf):
        for ent, xy in self.all_sorted_entities_to_render():
            self.draw_entity_at(ent, surf, xy)

        _, info_rect, inset = self.get_play_area_and_info_rects_and_inset(surf)

        self.draw_info(surf, self.get_top_bar_rect(surf), self.get_top_bar_text(), inset=inset)

        info_to_draw = self.get_info_text(line_spacing=inset)
        if info_to_draw is not None:
            self.draw_info(surf, info_rect, info_to_draw, bg_color=self.get_info_bg_color(), inset=inset)
        # pygame.draw.rect(surf, (255, 0, 0), info_rect, width=1)

    def get_play_area_and_info_rects_and_inset(self, surf):
        inset = 8
        info_h = 100
        top_bar_rect = self.get_top_bar_rect(surf)
        play_rect = (0, top_bar_rect[3], surf.get_width(), surf.get_height() - info_h - top_bar_rect[3])
        info_y = play_rect[1] + play_rect[3] - inset
        info_rect = (0, info_y, surf.get_width(), surf.get_height() - info_y)

        return play_rect, info_rect, inset

    def get_info_bg_color(self):
        return (0, 0, 0)

    def get_top_bar_rect(self, surf):
        return (0, 0, surf.get_width(), 28)

    def get_top_bar_text(self, sz="M"):
        res = []
        if self.in_progress_text is None:
            self.in_progress_text = (
                tr.TextRenderer("", size=sz, color=colors.get_white(), alignment=-1),
                tr.TextRenderer("", size=sz, color=colors.get_white(), alignment=1))
        self.in_progress_text[0].set_text(f"  Steps: {self.cur_state.step}")
        self.in_progress_text[1].set_text(f"Level: {self.cur_state.name}  ")
        res.append(self.in_progress_text)
        return res

    def get_info_text(self, line_spacing=4, sz="M"):
        res = []

        if not self.cur_state.is_player_alive():
            if self.you_died_text is None:
                self.you_died_text = tr.TextRenderer("", size=sz, color=colors.get_color(colors.RED_ID), alignment=0)
            self.you_died_text.set_text("You died!")
            res.append(self.you_died_text)
            res.append(line_spacing)
            if self.r_to_restart_text is None:
                self.r_to_restart_text = tr.TextRenderer("", size=sz, color=colors.get_white(), alignment=0)
            self.r_to_restart_text.set_text("Press [R] to restart, or [Z] to undo.")
            res.append(self.r_to_restart_text)
        elif self.cur_state.is_success():
            if self.success_text is None:
                self.success_text = tr.TextRenderer("", size=sz, color=colors.get_color(colors.GREEN_ID), alignment=0)
            self.success_text.set_text("Success!")
            res.append(self.success_text)
        else:
            if self.goal_text is None:
                self.goal_text = tr.TextRenderer("", size=sz, color=colors.get_white(), alignment=0)
            n_alive = self.cur_state.num_enemies_remaining()
            orig_alive = self.cur_state.get_initial_state().num_enemies_remaining()
            self.goal_text.set_text(f"Crush all enemies to win! ({(orig_alive - n_alive)}/{orig_alive})")
            res.append(self.goal_text)

            if self.dimension_text is None:
                self.dimension_text = tr.TextRenderer("", size=sz, color=colors.get_white(), alignment=0)
            cur_dim = self.cur_state.get_player_color()
            self.dimension_text.set_text(f"You're in the {colors.get_color_name(cur_dim, caps=True)} Dimension")
            self.dimension_text.set_color(colors.get_color(cur_dim))
            res.append(self.dimension_text)
            res.append(int(line_spacing * 2))

            if self.controls_text is None:
                self.controls_text = tr.TextRenderer("", size=sz, color=colors.get_white(), alignment=0)
            self.controls_text.set_text("[WASD] to Move, [Z] to Undo, [R] to Reset")
            res.append(self.controls_text)

        return res

    def draw_info(self, screen, rect, lines, bg_color=(0, 0, 0), inset=4):
        if bg_color is not None:
            pygame.draw.rect(screen, bg_color, rect)

        rect = utils.expand_rect(rect, -inset)

        y_offs = 0
        for l in lines:
            if isinstance(l, int):
                y_offs += l
                continue

            if not isinstance(l, tuple):
                l = (l,)
            line_h = 0
            for text in l:
                if text.get_alignment() == -1:
                    text.draw(screen, (rect[0], rect[1] + y_offs))
                elif text.get_alignment() == 1:
                    text.draw(screen, (rect[0] + rect[2] - text.get_size()[0], rect[1] + y_offs))
                else:
                    text.draw(screen, (int(rect[0] + rect[2] / 2 - text.get_size()[0] / 2), rect[1] + y_offs))
                line_h = max(line_h, text.get_size()[1])
            y_offs += line_h


_STATIONARY = 0
_DEAD = 1
_NEW = 2
_MOVING = 3


class AnimatedLevelRenderer(LevelRenderer):

    def __init__(self, state, trans_time=0.125, cell_size=32):
        super().__init__(state, cell_size=cell_size)
        self.trans_time = trans_time  # seconds

        self.spin_hz = 1
        self.fancy_radius = 0.25

        self.smoothing = True
        self.smooth_vel = 1 / self.trans_time  # cells / sec
        self._last_rendered_positions = {}

    def draw_entity_at(self, ent, surf, xy):
        xy_to_use = xy
        if not self.smoothing or ent not in self._last_rendered_positions:
            pass
        else:
            cur_time = inputs.get_time()
            last_xy, last_time = self._last_rendered_positions[ent]
            if last_time == cur_time:
                # not good, means we're drawing the same entity multiple times per frame
                pass
            else:
                d = utils.dist(last_xy, xy)
                if d < self.smooth_vel * (cur_time - last_time) or d > self.smooth_vel * self.trans_time * 2:
                    pass
                else:
                    v = utils.sub(xy, last_xy)
                    v = utils.set_length(v, self.smooth_vel * (cur_time - last_time))
                    xy_to_use = utils.add(last_xy, v)

        super().draw_entity_at(ent, surf, xy_to_use)
        self._last_rendered_positions[ent] = xy_to_use, inputs.get_time()

    def get_interp(self, cur_time=None):
        cur_time = inputs.get_time() if cur_time is None else cur_time
        if cur_time > self.prev_state_time + self.trans_time or self.prev_state is None:
            return 1
        else:
            return (cur_time - self.prev_state_time) / self.trans_time

    def get_offset_for_centering(self, screen: pygame.Surface, state=None, and_apply=True):
        interp = self.get_interp()
        if interp >= 1:
            return super().get_offset_for_centering(screen, state=state, and_apply=and_apply)
        else:
            prev_offs = super().get_offset_for_centering(screen, state=self.prev_state, and_apply=False)
            cur_offs = super().get_offset_for_centering(screen, state=self.cur_state, and_apply=False)
            offs = utils.interpolate(prev_offs, cur_offs, interp)
            if and_apply:
                self.set_offset(offs)
            return offs

    def all_sorted_entities_to_render(self):
        if self.cur_state is None:
            return ()

        walls = []
        nonwalls = []

        cur_time = inputs.get_time()
        interp = self.get_interp(cur_time=cur_time)

        if interp >= 1:
            # we're not mid-update
            for xy in self.cur_state.level:
                temp_nonwalls = []
                for ent in self.cur_state.level[xy]:
                    if ent.is_wall():
                        walls.append((ent, xy))
                    else:
                        temp_nonwalls.append((ent, xy))

                if len(temp_nonwalls) <= 1:
                    nonwalls.extend(temp_nonwalls)
                else:
                    for i, (ent, _) in enumerate(sorted(temp_nonwalls, key=lambda e_xy: e_xy[0].uid)):
                        t = 2 * math.pi * (cur_time * self.spin_hz + i / len(temp_nonwalls))
                        fancy_x = xy[0] + self.fancy_radius * math.cos(t)
                        fancy_y = xy[1] + self.fancy_radius * math.sin(t) / 2
                        nonwalls.append((ent, (fancy_x, fancy_y)))
        else:
            # we're interpolating
            cur_ents = {e_xy[0]: e_xy[1] for e_xy in self.cur_state.all_entity_positions()}
            old_ents = {e_xy[0]: e_xy[1] for e_xy in self.prev_state.all_entity_positions()}

            for e in cur_ents:
                if e.is_wall():
                    walls.append((e, cur_ents[e]))
                elif e not in old_ents:
                    nonwalls.append((e, cur_ents[e]))  # newly spawned?
                elif cur_ents[e] != old_ents[e]:
                    xy_interp = utils.interpolate(old_ents[e], cur_ents[e], interp, rounded=False)
                    nonwalls.append((e, xy_interp))  # it moved
                else:
                    nonwalls.append((e, cur_ents[e]))  # it didn't move
            for e in old_ents:
                if e not in cur_ents:
                    # NOTE: we're adding a Surface to nonwalls here (not an Entity)
                    # be careful~
                    spr = sprites.get_animated_sprite(sprites.EntityID.EXPLOSION, self.cell_size, interp,
                                                      color_id=e.color_id)
                    nonwalls.append((spr, utils.add(old_ents[e], (0, 0.001))))  # it died, render an explosion

        walls.sort(key=lambda w_xy: (w_xy[1][1], w_xy[1][0], hash(w_xy[0])))
        for w_xy in walls:
            yield w_xy

        nonwalls.sort(key=lambda e_xy: (e_xy[1][1], e_xy[1][0], hash(e_xy[0])))
        for e_xy in nonwalls:
            yield e_xy

