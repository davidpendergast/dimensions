import typing
import pygame
import src.sprites as sprites
import src.inputs as inputs

_UID_COUNTER = 1


def next_uid() -> int:
    global _UID_COUNTER
    _UID_COUNTER += 1
    return _UID_COUNTER - 1


def get_anim_idx():
    anim_speed = 4
    return int(inputs.get_time() * anim_speed)


class Entity:

    def __init__(self, ent_id: str, color_id: int, direction=(0, 1), art_direction=(1, 1), uid=None):
        self.uid = uid or next_uid()
        self.ent_id = ent_id
        self.color_id = color_id

        self.direction = (0, 1)
        self.art_direction = art_direction
        self.set_direction(direction)

    def set_direction(self, xy):
        art_dir = list(self.art_direction)
        if xy[0] != 0:
            art_dir[0] = xy[0]
        if xy[1] != 0:
            art_dir[1] = xy[1]
        self.art_direction = tuple(art_dir)
        self.direction = xy

    def copy(self) -> 'Entity':
        raise NotImplementedError()

    def get_sprite(self, size=16):
        return sprites.get_sprite(self.ent_id, size, self.color_id, self.art_direction, get_anim_idx())


class State:

    def __init__(self, color_id, step, prev=None):
        self.color_id = color_id
        self.step = step
        self.prev: typing.Optional['State'] = prev
        self.level: typing.Dict[typing.Tuple[int, int], typing.List[Entity]] = {}

    def add_entity(self, xy, ent):
        if xy not in self.level:
            self.level[xy] = []
        self.level[xy].append(ent)

    def copy(self) -> 'State':
        res = State(self.color_id, self.step, prev=self.prev)
        for xy in self.level:
            for e in self.level[xy]:
                res.add_entity(xy, e.copy())
        return res

    def get_next(self, player_dir) -> 'State':
        res = self.copy()
        res.prev = self
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

        return self

    def render_level(self, surf: pygame.Surface, pos, cellsize=32):
        for xy in self.level:
            for ent in self.level[xy]:
                ent_sprite = ent.get_sprite(cellsize)
                ent_xy = (pos[0] + cellsize * xy[0],
                          pos[1] + cellsize * xy[1])
                surf.blit(ent_sprite, ent_xy)


