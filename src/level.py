import typing
import pygame

_UID_COUNTER = 1

def next_uid() -> int:
    global _UID_COUNTER
    _UID_COUNTER += 1
    return _UID_COUNTER - 1


class EntityID:
    PLAYER = "p"
    H_WALKER = "h"
    V_WALKER = "v"
    WALL = "W"
    POTION = "c"
    BOX = "b"
    GOAL = "g"


class Entity:

    def __init__(self, ent_id: str, color_id: int, direction=(0, 1), uid=None):
        self.uid = uid or next_uid()
        self.ent_id = ent_id
        self.color_id = color_id
        self.direction = direction

    def copy(self) -> 'Entity':
        raise NotImplementedError()


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


