import json
import os.path
import traceback

import pygame
import typing

from functools import total_ordering

import configs
import src.sprites as sprites
import src.inputs as inputs
import src.colors as colors
import src.sounds as sounds
import src.utils as utils
import src.persistentdata as pd

_UID_COUNTER = 1


def next_uid() -> int:
    global _UID_COUNTER
    _UID_COUNTER += 1
    return _UID_COUNTER - 1


def get_anim_idx():
    anim_speed = 4
    return int(inputs.get_time() * anim_speed)


@total_ordering
class Entity:

    def __init__(self, ent_id: str, color_id: int, direction=(0, 1), art_direction=(1, 1), uid=None):
        self.uid = uid or next_uid()
        self.ent_id = ent_id
        self.color_id = color_id

        self.direction = direction
        self.art_direction = art_direction
        self.set_direction(direction)

    def __lt__(self, other):
        return self.color_id < other.color_id

    def __eq__(self, other):
        return self.uid == other.uid

    def __hash__(self):
        return self.uid

    def __repr__(self):
        return f"{type(self).__name__}({self.color_id}, {self.direction}, {self.uid})"

    def set_direction(self, xy):
        art_dir = list(self.art_direction)
        if xy[0] != 0:
            art_dir[0] = xy[0]
        if xy[1] != 0:
            art_dir[1] = xy[1]
        self.art_direction = tuple(art_dir)
        self.direction = xy

    def copy(self, dest=None) -> 'Entity':
        if dest is None:
            raise NotImplementedError()
        else:
            Entity.__init__(dest, self.ent_id, self.color_id, direction=self.direction,
                            art_direction=self.art_direction, uid=self.uid)
            return dest

    def get_sprite(self, size=16):
        return sprites.get_sprite(self.ent_id, size, self.color_id, self.art_direction, get_anim_idx())

    def is_pushable(self):
        return False

    def is_crushable(self):
        return False

    def is_solid(self):
        return True

    def is_wall(self):
        return isinstance(self, Wall)

    def is_box(self):
        return isinstance(self, Box)


class Box(Entity):

    def __init__(self, color_id=colors.BROWN_ID, uid=None):
        super().__init__(sprites.EntityID.BOX, color_id=color_id, uid=uid)

    def copy(self, dest=None):
        return super().copy(dest=dest or Box(color_id=self.color_id))

    def is_pushable(self):
        return True

    def is_solid(self):
        return True


class Wall(Entity):

    def __init__(self, color_id=colors.WHITE_ID, uid=None):
        super().__init__(sprites.EntityID.WALL, color_id=color_id, uid=uid)

    def copy(self, dest=None):
        return super().copy(dest=dest or Wall())

    def is_solid(self):
        return True

    def is_pushable(self):
        return False


class Player(Entity):

    def __init__(self, color_id: int, uid=None):
        super().__init__(sprites.EntityID.PLAYER, color_id, uid=uid)

    def is_pushable(self):
        return True

    def is_crushable(self):
        return False

    def is_solid(self):
        return False

    def copy(self, dest=None):
        return super().copy(dest=dest or Player(self.color_id))


class Enemy(Entity):

    def __init__(self, color_id: int, direction, uid=None):
        if direction == (0, 0):
            ent_id = sprites.EntityID.NO_WALKER
        elif direction[0] in (-1, 1) and direction[1] == 0:
            ent_id = sprites.EntityID.H_WALKER
        elif direction[0] == 0 and direction[1] in (-1, 1):
            ent_id = sprites.EntityID.V_WALKER
        else:
            raise ValueError(f"invalid direction for enemy: {direction}")

        super().__init__(ent_id, color_id, direction, uid=uid)

    def can_push(self):
        return False

    def is_pushable(self):
        return True

    def is_crushable(self):
        return True

    def is_solid(self):
        return False

    def copy(self, dest=None):
        return super().copy(dest=dest or Enemy(self.color_id, self.direction))


class Snek(Entity):

    def __init__(self, color_id=colors.YELLOW_ID, uid=None):
        super().__init__(sprites.EntityID.SNEK, color_id=color_id, uid=uid)

    def is_pushable(self):
        return True

    def is_crushable(self):
        return False

    def is_solid(self):
        return True

    def copy(self, dest=None):
        return super().copy(dest=dest or Snek(color_id=self.color_id))


class Potion(Entity):

    def __init__(self, color_id=colors.PINK_ID, uid=None):
        super().__init__(sprites.EntityID.POTION, color_id=color_id, uid=uid)

    def can_push(self):
        return False

    def is_pushable(self):
        return True

    def is_crushable(self):
        return True

    def is_solid(self):
        return False

    def copy(self, dest=None):
        return super().copy(dest=dest or Potion(self.color_id))


class WhatHappened:

    def __init__(self):
        self.moved: typing.Set[Entity] = set()
        self.crushed: typing.Set[Entity] = set()
        self.killed: typing.Set[Entity] = set()
        self.consumed: typing.Set[Entity] = set()
        self.colored: typing.Set[Entity] = set()
        self.turned: typing.Set[Entity] = set()

    def play_sounds(self):
        if utils.contains_type(self.moved, Box):
            sounds.play(sounds.BOX_MOVED)

        if utils.contains_type(self.killed, Player):
            sounds.play(sounds.PLAYER_KILLED)
        elif utils.contains_type(self.moved, Player):
            sounds.play(sounds.PLAYER_MOVED)
        elif utils.contains_type(self.moved, Enemy) or utils.contains_type(self.turned, Enemy):
            sounds.play(sounds.ENEMY_MOVED)
        else:
            sounds.play(sounds.PLAYER_SKIPPED)

        if utils.contains_type(self.killed, Enemy):
            sounds.play(sounds.ENEMY_KILLED)
        elif utils.contains_type(self.crushed, Potion):
            sounds.play(sounds.POTION_CRUSHED)
        elif utils.contains_type(self.consumed, Potion):
            sounds.play(sounds.POTION_CONSUMED)

    def __repr__(self):
        l = []
        if self.moved:
            l.append(f"moved:    {self.moved}")
        if self.crushed:
            l.append(f"crushed:  {self.crushed}")
        if self.killed:
            l.append(f"killed:   {self.killed}")
        if self.consumed:
            l.append(f"consumed: {self.consumed}")
        if self.colored:
            l.append(f"colored:  {self.colored}")
        if self.turned:
            l.append(f"turned:   {self.turned}")
        if len(l) > 0:
            l.insert(0, "")
        delim = '\n\t'
        return f"{type(self).__name__}({delim.join(l)})"


class State:

    def __init__(self, name, step=0, bounds=None, prev=None):
        self.name = name
        self.step = step
        self.prev: typing.Optional['State'] = prev
        self.level: typing.Dict[typing.Tuple[int, int], typing.List[Entity]] = {}
        self.bounds = bounds

        self.what_was = WhatHappened()  # note: not copied

    def copy(self) -> 'State':
        res = State(self.name, step=self.step, prev=self.prev)
        res.bounds = None if self.bounds is None else tuple(self.bounds)
        for xy in self.level:
            for e in self.level[xy]:
                res.add_entity(xy, e.copy())
        return res

    def get_area(self, cache=False):
        if self.bounds is None and cache and not len(self.level) == 0:
            self.bounds = utils.get_rect_containing_points(self.level.keys())

        if self.bounds is not None:
            return self.bounds
        else:
            return utils.get_rect_containing_points(self.level.keys())

    def get_xy(self, ent):
        # TODO this is real bad
        for xy in self.all_entity_positions(cond=lambda _e: _e == ent):
            return xy
        return None

    def is_in_bounds(self, xy):
        return self.bounds is None or utils.rect_contains(self.bounds, xy)

    def add_entity(self, xy, ent, ignore_bounds=False):
        if not ignore_bounds and not self.is_in_bounds(xy):
            raise ValueError(f"tried to add {ent} out of bounds: {xy}")
        if xy not in self.level:
            self.level[xy] = []
        self.level[xy].append(ent)

    def remove_entity(self, xy, ent):
        if xy not in self.level or ent not in self.level[xy]:
            raise ValueError(f"{ent} is not at {xy}, cannot remove it")
        else:
            self.level[xy].remove(ent)
            if len(self.level[xy]) == 0:
                del self.level[xy]

    def move_entity(self, from_xy, to_xy, entity, ignore_bounds=False):
        if from_xy != to_xy:
            self.remove_entity(from_xy, entity)
            self.add_entity(to_xy, entity, ignore_bounds=ignore_bounds)
            self.what_was.moved.add(entity)

    def all_entities_at(self, xy):
        if xy in self.level:
            for e in self.level[xy]:
                yield e

    def all_entities_with_type(self, ent_ids):
        if isinstance(ent_ids, str):
            ent_ids = (ent_ids,)
        for xy in self.level:
            for e in self.all_entities_at(xy):
                if e.ent_id in ent_ids:
                    yield e, xy

    def is_player_alive(self):
        for _ in self.all_entities_with_type(sprites.EntityID.PLAYER):
            return True
        return False

    def get_player_color(self):
        for p, _ in self.all_entities_with_type(sprites.EntityID.PLAYER):
            return p.color_id
        return colors.WHITE_ID

    def num_enemies_remaining(self):
        res = 0
        for e in self.all_entities_with_type(sprites.EntityID.all_enemies()):
            res += 1
        return res

    def get_initial_state(self):
        cur = self
        while cur.get_prev() is not None:  # infinite loop potential here, be careful
            cur = cur.get_prev()
        return cur

    def is_success(self):
        return self.num_enemies_remaining() == 0

    def all_coords_with_type(self, ent_ids):
        if isinstance(ent_ids, str):
            ent_ids = (ent_ids,)
        for xy in self.level:
            for e in self.all_entities_at(xy):
                if e.ent_id in ent_ids:
                    yield xy

    def all_entity_positions(self, cond=None):
        for xy in self.level:
            for e in self.all_entities_at(xy):
                if cond is None or cond(e):
                    yield e, xy

    def is_solid(self, xy, for_color_id=None):
        if not self.is_in_bounds(xy):
            return True
        for e in self.all_entities_at(xy):
            if e.is_solid() and (for_color_id is None or colors.can_interact(for_color_id, e.color_id)):
                return True
        return False

    def is_pushable(self, xy, pushing_color_id):
        if not self.is_in_bounds(xy):
            return False
        for e in self.all_entities_at(xy):
            if e.is_solid() and not e.is_pushable() and colors.can_interact(pushing_color_id, e.color_id):
                return False
        return True

    def try_to_push_cell_contents_recursively(self, start_xy, direction, pushing_color_id) -> bool:
        """returns: whether the pusher can enter this cell"""
        dest_xy = utils.add(start_xy, direction)
        if not self.is_solid(start_xy, pushing_color_id):
            # pusher can definitely enter this cell
            # push anything inside it out (which may crush them)
            for e in list(self.all_entities_at(start_xy)):
                if e.is_pushable() and colors.can_interact(pushing_color_id, e.color_id):
                    self.move_entity(start_xy, dest_xy, e, ignore_bounds=e.is_crushable())
            return True
        elif self.is_pushable(start_xy, pushing_color_id):
            # we can only move here iff we can push the contents out of the way
            colors_in_start_xy = set(e.color_id for e in self.all_entities_at(start_xy) if e.is_solid())
            if len(colors_in_start_xy) != 1:
                # based on the rules / entities available, there should only be one color in this cell if we're
                # in this state.
                raise ValueError(f"pushing a number of solid colors != 1?: {[e for e in self.all_entities_at(start_xy)]}")
            if self.try_to_push_cell_contents_recursively(dest_xy, direction, list(colors_in_start_xy)[0]):
                # we can enter, woo
                for e in list(self.all_entities_at(start_xy)):
                    if e.is_pushable() and colors.can_interact(pushing_color_id, e.color_id):
                        self.move_entity(start_xy, dest_xy, e)  # should never be going out of bounds here
                return True
            else:
                return False  # couldn't perform the push
        else:
            # it's solid and not pushable, can't enter
            return False

    def _try_to_move_player(self, player_dir):
        success = False
        if player_dir == (0, 0):
            success = True
        else:
            for (p, xy) in list(self.all_entities_with_type(sprites.EntityID.PLAYER)):
                dest_xy = utils.add(player_dir, xy)
                if not self.is_solid(dest_xy, for_color_id=p.color_id):
                    self.move_entity(xy, dest_xy, p)
                    success = True
                else:
                    # try to push
                    if self.try_to_push_cell_contents_recursively(dest_xy, player_dir, p.color_id):
                        self.move_entity(xy, dest_xy, p)
                        success = True

        for p, _ in self.all_entities_with_type(sprites.EntityID.PLAYER):
            if p.direction != player_dir:
                p.set_direction(player_dir)
                self.what_was.turned.add(p)

        return success

    def _remove_crushed_things(self):
        crushed = []
        for (e, xy) in self.all_entities_with_type(sprites.EntityID.all_crushables()):
            if self.is_in_bounds(xy):
                for e2 in self.all_entities_at(xy):
                    if e2 != e and e2.is_solid() and e2.color_id != e.color_id:
                        crushed.append((e, xy))
                        break
            else:
                crushed.append((e, xy))

        for (e, xy) in crushed:
            self.remove_entity(xy, e)
            self.what_was.crushed.add(e)
            self.what_was.killed.add(e)

    def _handle_direct_collisions(self, enemies_have_moved):
        types_we_care_about = (sprites.EntityID.PLAYER, sprites.EntityID.POTION) + sprites.EntityID.all_enemies()
        for xy in list(self.all_coords_with_type(types_we_care_about)):
            enemies = [e for e in self.all_entities_at(xy) if isinstance(e, Enemy)]
            players = [e for e in self.all_entities_at(xy) if isinstance(e, Player)]
            potions = [e for e in self.all_entities_at(xy) if isinstance(e, Potion)]

            enemies.sort()
            players.sort()
            potions.sort()

            used_potion = False
            for e in players + enemies:
                orig_color = e.color_id
                any_pot_had_orig_color = False
                for pot in potions:
                    if e.color_id != pot.color_id:
                        e.color_id = pot.color_id
                        self.what_was.colored.add(e)
                        used_potion = True
                    if pot.color_id == orig_color:
                        any_pot_had_orig_color = True
                if e.color_id != orig_color and any_pot_had_orig_color:
                    e.color_id = orig_color  # trust me, this is logical

            # if any potion got used, remove all potions (again, logical)
            if used_potion:
                for pot in potions:
                    self.remove_entity(xy, pot)
                    self.what_was.consumed.add(pot)

            # handle collisions with enemies
            for p in players:
                for e in enemies:
                    if p.color_id != e.color_id:
                        if enemies_have_moved or utils.add(p.direction, e.direction) == (0, 0):
                            self.remove_entity(xy, p)
                            self.what_was.killed.add(p)

    def _turn_enemies(self):
        for e, xy in list(self.all_entities_with_type(sprites.EntityID.all_enemies())):
            e_dir = e.direction
            dest_xy = utils.add(xy, e_dir)
            if self.is_solid(dest_xy, for_color_id=e.color_id):
                e_dir = utils.sub((0, 0), e_dir)
                if e.direction != e_dir:
                    e.set_direction(e_dir)
                    self.what_was.turned.add(e)

    def _move_enemies(self):
        for e, xy in list(self.all_entities_with_type(sprites.EntityID.all_enemies())):
            e_dir = e.direction
            dest_xy = utils.add(xy, e_dir)
            if not self.is_solid(dest_xy, for_color_id=e.color_id):
                self.move_entity(xy, dest_xy, e)

    def get_next(self, player_dir) -> 'State':
        res = self.copy()
        res.prev = self
        res.step += 1

        # move player
        res._try_to_move_player(player_dir)

        # check for things player just crushed
        res._remove_crushed_things()

        # handle collisions between enemies, players, and potions
        res._turn_enemies()
        res._handle_direct_collisions(False)

        res._move_enemies()
        res._handle_direct_collisions(True)

        return res

    def get_prev(self):
        return self.prev

    def render_level(self, surf: pygame.Surface, pos, cellsize=32):
        for xy in self.level:
            for ent in self.level[xy]:
                ent_sprite = ent.get_sprite(cellsize)
                ent_xy = (pos[0] + cellsize * xy[0],
                          pos[1] + cellsize * xy[1])
                surf.blit(ent_sprite, ent_xy)

    def save_to_json(self, filepath) -> typing.Optional[dict]:
        try:
            blob = {
                pd.VERSION_KEY: configs.VERSION,
                NAME_TAG: self.name,
                DATA_TAG: []
            }

            area = self.get_area()
            for y in range(area[1], area[1] + area[3]):
                row_items = []
                for x in range(area[0], area[0] + area[2]):
                    ents_at_xy = list(self.all_entities_at((x, y)))
                    row_items.append(_encode_ents(ents_at_xy))
                blob[DATA_TAG].append(" ".join(row_items))

            if filepath is not None:
                print(f"INFO: saving {blob[NAME_TAG]} to {filepath}\n" +
                      "\n".join(blob[DATA_TAG]))
                with open(filepath, 'w') as f:
                    json.dump(blob, f)

            return blob
        except:
            print("ERROR: failed to save level")
            traceback.print_exc()
            return None


NAME_TAG = "name"
DATA_TAG = "data"

PLAYER_PREFIX = "P"
WALL_PREFIX = "W"
POTION_PREFIX = "p"
ENEMY_PREFIXES = {"U": (0, -1), "D": (0, 1), "L": (-1, 0), "R": (1, 0),  "N": (0, 0)}
SNEK_PREFIX = "S"
BOX_PREFIX = "B"

sample_blob = {
    NAME_TAG: "Blocks",
    DATA_TAG: [
        "W0 W0 W0 W0 W0 W0 W0 W0 W0 W0",
        "W0                p3       W0",
        "W0                         W0",
        "W0       P1       B6       W0",
        "W0                L2       W0",
        "W0                         W0",
        "W0 W0 W0 W0 W0 W0 W0 W0 W0 W0",
    ]
}

_OBJ_CREATOR = {
    PLAYER_PREFIX: lambda c: Player(color_id=c),
    WALL_PREFIX: lambda c: Wall(color_id=c),
    POTION_PREFIX: lambda c: Potion(color_id=c),
    BOX_PREFIX: lambda c: Box(color_id=c),
    SNEK_PREFIX: lambda c: Snek(color_id=c),
}
for _pfx in ENEMY_PREFIXES:
    _OBJ_CREATOR[_pfx] = lambda c: Enemy(c, ENEMY_PREFIXES[_pfx])


def from_json(blob) -> State:
    name = str(blob[NAME_TAG])
    res = State(name)
    for y in range(len(blob[DATA_TAG])):
        row = blob[DATA_TAG][y]
        for i in range(0, len(row), 3):
            prefix = row[i:i+1]
            if prefix == ' ':
                continue
            else:
                color_id = int(row[i+1:i+2])
                obj = _OBJ_CREATOR[prefix](color_id)

                x = i // 3
                res.add_entity((x, y), obj)
    res.get_area(cache=True)
    return res


def _encode_ents(ents) -> str:
    if len(ents) == 0:
        return "  "
    elif len(ents) > 1:
        print(f"WARN: cannot encode stack of entities: {ents} (choosing first)")
        return _encode_ents((ents[0],))
    else:
        ent = ents[0]
        color_str = str(utils.bound(ent.color_id, colors.WHITE_ID, colors.BROWN_ID))
        prefix = None
        if isinstance(ent, Player):
            prefix = PLAYER_PREFIX
        elif isinstance(ent, Enemy):
            for prf in ENEMY_PREFIXES:
                if ent.direction == ENEMY_PREFIXES[prf]:
                    prefix = prf
                    break
            if prefix is None:
                print(f"WARN: enemy has invalid direction: {ent}, dir={ent.direction} (not saving it).")
        elif isinstance(ent, Box):
            prefix = BOX_PREFIX
        elif isinstance(ent, Wall):
            prefix = WALL_PREFIX
        elif isinstance(ent, Snek):
            prefix = SNEK_PREFIX
        elif isinstance(ent, Potion):
            prefix = POTION_PREFIX

        if prefix is None:
            print(f"WARN: an entity couldn't be saved: {ent}")
            return "  "
        else:
            return prefix + color_str







