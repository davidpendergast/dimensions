import src.level as level
import src.colors as colors


def make_demo_state():
    state = level.State("Demo")

    state.add_entity((4, 4), level.Player(colors.RED_ID))
    state.add_entity((5, 2), level.Wall())
    state.add_entity((5, 3), level.Wall())
    state.add_entity((5, 4), level.Wall())
    state.add_entity((6, 4), level.Wall())
    state.add_entity((7, 4), level.Wall())
    state.add_entity((6, 5), level.Enemy(colors.GREEN_ID, (-1, 0)))
    state.add_entity((2, 5), level.Box())
    state.add_entity((3, 6), level.Box())
    state.add_entity((5, 7), level.Box())
    state.add_entity((8, 5), level.Potion(colors.PINK_ID))

    state.get_area(cache=True)
    return state


def make_demo_state2(dims):
    import random

    state = level.State("Demo 2")
    for x in range(dims[0]):
        for y in range(dims[1]):
            xy = (x, y)
            if x == 0 or y == 0 or x == dims[0] - 1 or y == dims[1] - 1 or random.random() < 0.2:
                if random.random() < 0.1:
                    wall_color_id = colors.rand_color_id()
                else:
                    wall_color_id = colors.WHITE_ID
                state.add_entity(xy, level.Wall(color_id=wall_color_id))
            elif random.random() < 0.2:
                if random.random() < 0.8:
                    box_color_id = random.randint(0, colors.YELLOW_ID)
                else:
                    box_color_id = colors.BROWN_ID
                state.add_entity(xy, level.Box(color_id=box_color_id))
            elif random.random() <= 0.1:
                state.add_entity(xy, level.Potion(random.randint(0, colors.YELLOW_ID)))
            elif random.random() <= 0.1:
                direction = random.choice([(-1, 0), (1, 0), (0, 1), (0, -1), (0, 0)])
                state.add_entity(xy, level.Enemy(random.randint(0, colors.YELLOW_ID), direction))

    p_xy = random.randint(1, dims[0] - 2), random.randint(1, dims[1] - 2)
    for e in list(state.all_entities_at(p_xy)):
        state.remove_entity(p_xy, e)
    state.add_entity(p_xy, level.Player(colors.RED_ID))
    state.get_area(cache=True)

    return state


def make_demo_from_json():
    return level.from_json(level.sample_blob)
