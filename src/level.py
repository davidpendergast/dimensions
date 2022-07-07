import pygame
import typing
from functools import total_ordering

import src.sprites as sprites
import src.inputs as inputs
import src.colors as colors
import src.utils as utils

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


class Box(Entity):

    def __init__(self, uid=None):
        super().__init__(sprites.EntityID.BOX, color_id=colors.BROWN_ID, uid=uid)

    def copy(self, dest=None):
        return super().copy(dest=dest or Box())

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


class Potion(Entity):

    def __init__(self, color_id):
        super().__init__(sprites.EntityID.POTION, color_id)

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


class State:

    def __init__(self, color_id, step=0, prev=None):
        self.color_id = color_id
        self.step = step
        self.prev: typing.Optional['State'] = prev
        self.level: typing.Dict[typing.Tuple[int, int], typing.List[Entity]] = {}

    def copy(self) -> 'State':
        res = State(self.color_id, step=self.step, prev=self.prev)
        for xy in self.level:
            for e in self.level[xy]:
                res.add_entity(xy, e.copy())
        return res

    def add_entity(self, xy, ent):
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

    def move_entity(self, from_xy, to_xy, entity):
        self.remove_entity(from_xy, entity)
        self.add_entity(to_xy, entity)

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

    def all_coords_with_type(self, ent_ids):
        if isinstance(ent_ids, str):
            ent_ids = (ent_ids,)
        for xy in self.level:
            for e in self.all_entities_at(xy):
                if e.ent_id in ent_ids:
                    yield xy

    def is_empty(self, xy):
        for _ in self.all_entities_at(xy):
            return True
        return False

    def is_solid(self, xy, for_color_id=None):
        for e in self.all_entities_at(xy):
            if e.is_solid() and (for_color_id is None or e.color_id != for_color_id):
                return True
        return False

    def is_pushable(self, xy):
        for e in self.all_entities_at(xy):
            if e.is_solid() and not e.is_pushable():
                return False
        return True

    def try_to_push_recursively(self, start_xy, direction) -> bool:
        dest_xy = utils.add(start_xy, direction)
        if not self.is_solid(start_xy):
            for e in list(self.all_entities_at(start_xy)):
                if e.is_pushable():
                    self.move_entity(start_xy, dest_xy, e)
            return True
        elif not self.is_pushable(start_xy):
            return False  # something solid that can't be pushed
        else:
            # there's something solid, but pushable there
            can_push = self.try_to_push_recursively(dest_xy, direction)
            if not can_push:
                return False
            else:
                for e in list(self.all_entities_at(start_xy)):
                    if e.is_solid() and e.is_pushable():
                        self.move_entity(start_xy, dest_xy, e)
                return True

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
                    if self.try_to_push_recursively(dest_xy, player_dir):
                        self.move_entity(xy, dest_xy, p)
                        success = True
        if success:
            for p, _ in self.all_entities_with_type(sprites.EntityID.PLAYER):
                p.set_direction(player_dir)
        return success

    def _remove_crushed_things(self):
        crushed = []
        for e, xy in self.all_entities_with_type(sprites.EntityID.all_crushables()):
            for e2 in self.all_entities_at(xy):
                if e2 != e and e2.is_solid() and e2.color_id != e.color_id:
                    crushed.append((e, xy))
                    break
        for e_xy in crushed:
            self.remove_entity(e_xy[1], e_xy[0])

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
                        used_potion = True
                    if pot.color_id == orig_color:
                        any_pot_had_orig_color = True
                if e.color_id != orig_color and any_pot_had_orig_color:
                    e.color_id = orig_color  # trust me, this is logical

            # if any potion got used, remove all potions (again, logical)
            if used_potion:
                for pot in potions:
                    self.remove_entity(xy, pot)

            # handle collisions with enemies
            for p in players:
                for e in enemies:
                    if p.color_id != e.color_id:
                        if enemies_have_moved or utils.add(p.direction, e.direction) == (0, 0):
                            self.remove_entity(xy, p)

    def _turn_enemies(self):
        for e, xy in list(self.all_entities_with_type(sprites.EntityID.all_enemies())):
            e_dir = e.direction
            dest_xy = utils.add(xy, e_dir)
            if self.is_solid(dest_xy, for_color_id=e.color_id):
                e_dir = utils.sub((0, 0), e_dir)
                e.set_direction(e_dir)

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
        # Movement Rules:
        # 1. Player moves first, pushing any boxes in its path.
        # 2. Enemies move second, changing direction if they run into a wall or box.
        # 3. Boxes push other boxes, enemies, and potions, and cannot pass through walls.
        # 4. Potions and enemies cannot push boxes (even if the player is pushing them with another box).
        # 5. If pushed and there's no space to move into, potions and enemies will be crushed.
        # 6. If the player moves into an enemy, or an enemy moves into the player, the player is killed.
        # 7. If the player or an enemy moves into a potion, or has it moved into them, they will become that color.
        # 8. Objects of the same color do not interact.
        # 9. The player, walls, enemies, and potions can have color.
        # 10. Boxes do not interact with walls or enemies of the player's color.
        # 11. Enemies disappear when player becomes their color(?).
        # 12. To beat the level, destroy all enemies.

        # move player
        if not res._try_to_move_player(player_dir):
            return self  # can't move that way

        # check for things player just crushed
        res._remove_crushed_things()

        # handle collisions between enemies, players, and potions
        res._turn_enemies()
        res._handle_direct_collisions(False)

        res._move_enemies()
        res._handle_direct_collisions(True)

        return res

    def render_level(self, surf: pygame.Surface, pos, cellsize=32):
        for xy in self.level:
            for ent in self.level[xy]:
                ent_sprite = ent.get_sprite(cellsize)
                ent_xy = (pos[0] + cellsize * xy[0],
                          pos[1] + cellsize * xy[1])
                surf.blit(ent_sprite, ent_xy)


