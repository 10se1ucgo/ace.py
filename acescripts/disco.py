"""
"Ever wanted a disco in Ace of Spades?"

Creator: 10se1ucgo
"""
import asyncio

import itertools

from aceserver import types
from aceserver.protocol import ServerProtocol
from aceserver.connection import ServerConnection
from acemodes import GameMode
from acescripts import Script, commands


COLORS = [
    (251,  76,   0),
    (119, 215, 118),
    ( 37,  78, 235),
    (222, 209,   2),
    (224, 113, 234),
    (255, 255, 255)
]


class DiscoScript(Script):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        GameMode.on_game_end += self.on_game_end

        self.disco_sound = self.protocol.create_sound("disco", looping=True)
        self.disco_task: asyncio.Task = None

    def deinit(self):
        if self.disco_task:
            self.disco_task.cancel()

    @commands.command(name="disco")
    async def disco_cmd(self, connection: ServerConnection):
        return await self.toggle_disco()

    async def toggle_disco(self):
        if not self.disco_task or self.disco_task.cancelled():
            await self.protocol.broadcast_server_message("DISCO PARTY MODE ENABLED!")
            self.disco_task = self.protocol.loop.create_task(self.disco())
            await self.disco_sound.play()
        else:
            await self.protocol.broadcast_server_message("The party has been stopped.")
            self.disco_task.cancel()
            self.disco_task = None
            await self.disco_sound.stop()

    async def disco(self, num=None):
        original = self.protocol.fog_color
        try:
            if num == None:  # infinite
                iterator = itertools.cycle(COLORS)
            else:
                iterator = itertools.chain.from_iterable(itertools.repeat(COLORS, num))
            for color in iterator:
                await self.protocol.set_fog_color(*color, save=False)
                await asyncio.sleep(1/3)
        finally:
            await self.protocol.set_fog_color(*original)

    async def on_game_end(self, winner: types.Team):
        await self.disco(3)


def init(protocol: ServerProtocol):
    return DiscoScript(protocol)
