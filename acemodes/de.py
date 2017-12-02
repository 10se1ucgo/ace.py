import asyncio
from typing import *

from acelib.constants import *
from acemodes import GameMode
from aceserver import types
from aceserver.protocol import ServerProtocol
from aceserver.connection import ServerConnection


class C4(types.Flag):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.planter = None


class Defusal(GameMode):
    name = "Defusal"
    score_limit = 10

    async def init(self):
        await super().init()
        self.counter_terrorists = self.protocol.team1
        self.counter_terrorists.name = "Counter-Terrorists"
        self.counter_terrorists.color = (93,121,174)
        self.terrorists = self.protocol.team2
        self.terrorists.name = "Terrorists"
        self.terrorists.color = (222,155,53)

        self.c4_time = 40

        self.bomb: C4 = \
            await self.protocol.create_entity(C4, position=self.get_random_pos(self.terrorists), team=self.counter_terrorists)
        types.Flag.on_collide += self.on_pickup_bomb

        self.bombsite_a: types.CommandPost = \
            await self.protocol.create_entity(types.CommandPost, position=self.get_random_pos(self.counter_terrorists))
        self.bombsite_b: types.CommandPost = \
            await self.protocol.create_entity(types.CommandPost, position=self.get_random_pos(self.counter_terrorists))
        types.CommandPost.on_collide += self.on_site_collide

        self.plant_call = None

        self.c4plant = self.protocol.create_sound("c4plant")

    async def deinit(self):
        self.bomb.destroy()
        self.bombsite_a.destroy()
        self.bombsite_b.destroy()

    async def on_pickup_bomb(self, bomb: C4, player: ServerConnection):
        if bomb is not self.bomb: return

        if player.team is self.terrorists:
            if bomb.planter: return
            await bomb.set_carrier(player)
            await self.protocol.broadcast_hud_message(f"{player} picked up the bomb.")
        elif player.team is self.counter_terrorists and bomb.planter is not None:
            pass # todo

    async def on_site_collide(self, site: types.CommandPost, player: ServerConnection):
        if self.bomb.carrier is not player or player.team is not self.terrorists: return
        if self.bomb.planter: return

        if self.protocol.time - player.store.get("de_last_plant", 0) >= 3:
            if not self.plant_call or self.plant_call.done():
                self.plant_call = self.protocol.loop.create_task(self.delay_plant(player))
            player.store["de_last_plant"] = self.protocol.time

    async def delay_plant(self, player: ServerConnection):
        x, y, z = player.position.xyz
        for _ in reversed(range(5)):
            await player.set_position(x, y, z)
            if player.tool_type != TOOL.BLOCK:
                return
            await player.send_server_message(f"Planting, {_ + 1} seconds remaining.")
            await asyncio.sleep(1)
        await self.plant_bomb(player)

    async def plant_bomb(self, player: ServerConnection):
        await self.bomb.set_carrier(None)
        await self.bomb.set_team(player.team)
        await self.bomb.set_position(*player.position.xyz)
        self.bomb.planter = player

        await self.protocol.broadcast_hud_message(f"{player} planted the bomb.")
        await self.c4plant.play()
        self.protocol.loop.create_task(self.play_sounds())

    async def play_sounds(self):
        c4beep = self.protocol.create_sound("c4beep", position=self.bomb.position.xyz)
        det = self.protocol.time + self.c4_time
        while self.protocol.time < det:
            percentage = (det - self.protocol.time) / self.c4_time
            await c4beep.play()
            await asyncio.sleep(percentage + .1)
        await self.protocol.broadcast_hud_message("Boom.")


def init(protocol: ServerProtocol):
    return Defusal(protocol)
