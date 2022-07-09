import typing
import random
import math

import src.level as level
import src.inputs as inputs
import src.utils as utils


class LevelRenderer:

    def __init__(self, state, cell_size=32):
        self.cur_state: level.State = state
        self.prev_state: typing.Optional[level.State] = None
        self.prev_state_time = 0

        self.xy_offset = (0, 0)
        self.cell_size = cell_size

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
        self.xy_offset = offs_xy

    def update(self):
        pass

    def draw_entity_at(self, ent, surf, xy):
        ent_sprite = ent.get_sprite(self.cell_size)
        ent_xy = (round(self.xy_offset[0] + self.cell_size * xy[0]),
                  round(self.xy_offset[1] + self.cell_size * xy[1]))
        surf.blit(ent_sprite, ent_xy)

    def draw(self, surf):
        if self.cur_state is not None:
            for xy in self.cur_state.level:
                for ent in self.cur_state.level[xy]:
                    self.draw_entity_at(ent, surf, xy)


_STATIONARY = 0
_DEAD = 1
_NEW = 2
_MOVING = 3


class AnimatedLevelRenderer(LevelRenderer):

    def __init__(self, state, trans_time=0.125, cell_size=32):
        super().__init__(state, cell_size=cell_size)
        self.trans_time = trans_time  # seconds

        self.fancy_overlaps = True
        self.spin_hz = 1
        self.fancy_radius = 0.25

    def draw(self, surf):
        cur_time = inputs.get_time()
        if cur_time > self.prev_state_time + self.trans_time or self.prev_state is None:
            if not self.fancy_overlaps:
                super().draw(surf)
            else:
                if self.cur_state is not None:
                    for xy in self.cur_state.level:
                        nonwalls = []
                        for ent in self.cur_state.level[xy]:
                            if ent.is_wall():
                                self.draw_entity_at(ent, surf, xy)
                            else:
                                nonwalls.append(ent)

                        if len(nonwalls) <= 1:
                            for ent in nonwalls:
                                self.draw_entity_at(ent, surf, xy)
                        else:
                            to_draw = []
                            for i, ent in enumerate(sorted(nonwalls, key=lambda _ent: _ent.uid)):
                                t = 2 * math.pi * (cur_time * self.spin_hz + i / len(nonwalls))
                                fancy_x = xy[0] + self.fancy_radius * math.cos(t)
                                fancy_y = xy[1] + self.fancy_radius * math.sin(t) / 2
                                to_draw.append((fancy_y, fancy_x, ent))

                            to_draw.sort()
                            for (y, x, ent) in to_draw:
                                self.draw_entity_at(ent, surf, (x, y))
        else:
            cur_ents = {e_xy[0]: e_xy[1] for e_xy in self.cur_state.all_entity_positions()}
            old_ents = {e_xy[0]: e_xy[1] for e_xy in self.prev_state.all_entity_positions()}
            interp = (cur_time - self.prev_state_time) / self.trans_time

            to_render = []

            for e in old_ents:
                if e not in cur_ents:
                    to_render.append((old_ents[e], e, _DEAD))
                elif old_ents[e] != cur_ents[e]:
                    xy_interp = utils.interpolate(old_ents[e], cur_ents[e], interp, rounded=False)
                    to_render.append((xy_interp, e, _MOVING))
                else:
                    to_render.append((cur_ents[e], e, _STATIONARY))
            for e in cur_ents:
                if e not in old_ents:
                    to_render.append((cur_ents[e], e, _NEW))

            to_render.sort(key=lambda e_tup: (e_tup[0][1], e_tup[2], random.random()))

            for xy, ent, ent_state in to_render:
                self.draw_entity_at(ent, surf, xy)
                