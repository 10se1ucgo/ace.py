from typing import *

from acelib.math3d import Vector3
from acemodes import GameMode
from aceserver import protocol, connection, types



class CTF(GameMode):
    name = "CTF"
    score_limit = 10

    async def init(self):
        await super().init()

        team1 = self.protocol.team1
        team2 = self.protocol.team2

        self.team1_intel: types.Flag = \
            await self.protocol.create_entity(types.Flag, position=self.get_random_pos(team1), team=team1)
        self.team2_intel: types.Flag = \
            await self.protocol.create_entity(types.Flag, position=self.get_random_pos(team2), team=team2)
        self.intels = {self.team1_intel.team: self.team1_intel, self.team2_intel.team: self.team2_intel}
        types.Flag.on_collide += self.on_intel_collide

        self.team1_cp: types.CommandPost = \
            await self.protocol.create_entity(types.CommandPost, position=self.get_random_pos(team1), team=team1)
        self.team2_cp: types.CommandPost = \
            await self.protocol.create_entity(types.CommandPost, position=self.get_random_pos(team2), team=team2)
        self.cps = {self.team1_cp.team: self.team1_cp, self.team2_cp.team: self.team2_cp}
        types.CommandPost.on_collide += self.on_cp_collide

        self.pickup_sound = self.protocol.create_sound("pickup")
        self.capture_sound = self.protocol.create_sound("horn")

    async def deinit(self):
        [await intel.destroy() for intel in self.intels.values()]
        [await cp.destroy() for cp in self.cps.values()]

    async def on_intel_collide(self, intel: types.Flag, player: 'connection.ServerConnection'):
        # print(intel, player)
        if intel.team == player.team:
            return

        await intel.set_carrier(player)
        await self.protocol.broadcast_hud_message(f"{player} picked up the {intel.team} Intel")
        await self.pickup_sound.play()

    async def on_cp_collide(self, base: types.CommandPost, player: 'connection.ServerConnection'):
        # print(base, player)
        if base.team != player.team:
            return

        if self.protocol.time - player.store.get("ctf_last_restock", 0) >= 3:
            await player.restock()
            player.store["ctf_last_restock"] = self.protocol.time

        intel = self.intels[player.team.other]
        if intel.carrier == player:
            await self.capture_intel(player, intel)

    async def capture_intel(self, player, intel):
        await self.reset_intel(intel)
        player.team.score += 1
        await player.team.set_score()
        await self.protocol.broadcast_hud_message(f"{player} captured the {intel.team} Intel")
        await self.capture_sound.play()

    def get_spawn_point(self, player: 'connection.ServerConnection') -> Tuple[int, int, int]:
        pos: Vector3 = self.team1_intel.position - Vector3(3, 3, 0)
        pos.z = self.protocol.map.get_z(pos.x, pos.y) - 2
        return pos.xyz

    async def reset_intel(self, intel):
        await intel.set_carrier(None)
        await intel.set_position(*self.get_random_pos(intel.team))
