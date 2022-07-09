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

    def all_sorted_entities_to_render(self):
        if self.cur_state is not None:
            for xy in self.cur_state.level:
                for ent in self.cur_state.level[xy]:
                    yield ent, xy

    def draw_entity_at(self, ent, surf, xy):
        ent_sprite = ent.get_sprite(self.cell_size)
        ent_xy = (round(self.xy_offset[0] + self.cell_size * xy[0]),
                  round(self.xy_offset[1] + self.cell_size * xy[1]))
        surf.blit(ent_sprite, ent_xy)

    def draw(self, surf):
        for ent, xy in self.all_sorted_entities_to_render():
            self.draw_entity_at(ent, surf, xy)


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

    def all_sorted_entities_to_render(self):
        if self.cur_state is None:
            return ()

        walls = []
        nonwalls = []

        cur_time = inputs.get_time()
        if cur_time > self.prev_state_time + self.trans_time or self.prev_state is None:
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
            interp = (cur_time - self.prev_state_time) / self.trans_time

            for e in cur_ents:
                if e not in old_ents:
                    nonwalls.append((e, cur_ents[e]))  # newly spawned?
                elif cur_ents[e] != old_ents[e]:
                    xy_interp = utils.interpolate(old_ents[e], cur_ents[e], interp, rounded=False)
                    nonwalls.append((e, xy_interp))  # it moved
                else:
                    nonwalls.append((e, cur_ents[e]))  # it didn't move
            for e in old_ents:
                if e not in cur_ents:
                    nonwalls.append((e, old_ents[e]))  # it died

        walls.sort(key=lambda w_xy: (w_xy[1][1], w_xy[1][0], w_xy[0]))
        for w_xy in walls:
            yield w_xy

        nonwalls.sort(key=lambda e_xy: (e_xy[1][1], e_xy[1][0], e_xy[0]))
        for e_xy in nonwalls:
            yield e_xy

