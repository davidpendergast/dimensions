import pygame

import src.utils as utils
import src.colors as colors

SHEET = None
BASE_SPRITES = {}
_CACHE = {}


class EntityID:
    PLAYER = "p"
    H_WALKER = "h"
    V_WALKER = "v"
    NO_WALKER = "n"
    SNEK = "s"
    WALL = "W"
    POTION = "c"
    BOX = "b"
    GOAL = "g"

    EXPLOSION = "e"
    BIG_PLAYER = "PBIG"
    BIG_V_WALKER = "VBIG"

    @staticmethod
    def all_enemies():
        return (EntityID.H_WALKER, EntityID.V_WALKER, EntityID.NO_WALKER)

    @staticmethod
    def all_crushables():
        return EntityID.all_enemies() + (EntityID.POTION, EntityID.SNEK)

    @staticmethod
    def all_pushables():
        return (EntityID.BOX,) + EntityID.all_crushables()

    @staticmethod
    def all_solids():
        return (EntityID.WALL, EntityID.BOX)


def load():
    global SHEET, BASE_SPRITES
    img_path = utils.asset_path("assets/assets.png")
    SHEET = pygame.image.load(img_path).convert_alpha()

    def imgs(xs, ys, w=16, h=16):
        ys = (ys,) if isinstance(ys, int) else ys
        xs = (xs,) if isinstance(xs, int) else xs
        res = []
        for y in ys:
            for x in xs:
                res.append(SHEET.subsurface(x, y, w, h))
        return res

    BASE_SPRITES[EntityID.PLAYER] = imgs((0, 16), 0)
    BASE_SPRITES[EntityID.H_WALKER] = imgs((0, 16), 16)
    BASE_SPRITES[EntityID.V_WALKER] = imgs((0, 16, 32, 48), 32)
    BASE_SPRITES[EntityID.NO_WALKER] = imgs((16, 32), 48)
    BASE_SPRITES[EntityID.WALL] = imgs(32, 0)
    BASE_SPRITES[EntityID.SNEK] = imgs((32, 48), 16)
    BASE_SPRITES[EntityID.POTION] = imgs(0, 48)
    BASE_SPRITES[EntityID.BOX] = imgs(48, 0)
    BASE_SPRITES[EntityID.EXPLOSION] = imgs((64, 80, 96, 112), (0, 16, 32))
    BASE_SPRITES[EntityID.BIG_PLAYER] = imgs(0, 64, w=64, h=64)
    BASE_SPRITES[EntityID.BIG_V_WALKER] = imgs(64, 64, w=64, h=64)


def clear_cache():
    _CACHE.clear()


def _recolor_slow(surf: pygame.Surface, start_color, end_color):
    # slow operation, make sure to cache the result
    res = surf.copy()
    for x in range(res.get_width()):
        for y in range(res.get_height()):
            if res.get_at((x, y)) == start_color:
                res.set_at((x, y), end_color)
    return res


def _recolor_fast(surf: pygame.Surface, end_color):
    res = surf.copy()
    res.fill(end_color)
    res.blit(surf, (0, 0), surf.get_rect(), special_flags=pygame.BLEND_MULT)
    return res


def _get_sprite(key, nocache=False):
    ent_id, size, color_id, direction, anim_idx = key
    base_sprites = BASE_SPRITES[ent_id]
    if len(base_sprites) == 4 and ent_id == EntityID.V_WALKER:
        base_sprites = base_sprites[0:2] if direction[1] >= 0 else base_sprites[2:4]

    anim_idx = anim_idx % len(base_sprites)
    key = ent_id, size, color_id, direction, anim_idx

    if key not in _CACHE:
        sprite: pygame.Surface = base_sprites[anim_idx]
        if direction[0] < 0 and ent_id in (EntityID.PLAYER, EntityID.H_WALKER,
                                           EntityID.V_WALKER, EntityID.SNEK):
            sprite = pygame.transform.flip(sprite, True, False)

        sprite = _recolor_slow(sprite, (255, 255, 255), colors.get_color(color_id))

        if sprite.get_size() != size:
            sprite = pygame.transform.scale(sprite, (size, size))

        if nocache:
            return sprite
        _CACHE[key] = sprite

    return _CACHE[key]


def get_sprite(ent_id, size, color_id=0, direction=(0, 1), anim_idx=0):
    key = (ent_id, size, color_id, direction, anim_idx)
    return _get_sprite(key)


def get_animated_sprite(ent_id, size, prog, color_id=0, direction=(0, 1)):
    base_sprites = BASE_SPRITES[ent_id]
    idx = max(0, min(len(base_sprites), int(prog * (len(base_sprites)))))
    return get_sprite(ent_id, size, color_id=color_id, direction=direction, anim_idx=idx)