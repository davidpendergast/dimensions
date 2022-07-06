import asyncio

import src.game as game


async def main():
    g = game.Game((640, 480), fps=60)
    await g.start()


if __name__ == "__main__":
    asyncio.run( main() )
