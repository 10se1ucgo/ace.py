from typing import *

from acelib.constants import *
from acelib.math3d import Vector3
from acemodes import GameMode
from aceserver import protocol, entity, connection



class CTF(GameMode):
    name = "CTF"
    score_limit = 10

    async def init(self):
        team1 = self.protocol.team1
        team2 = self.protocol.team2

        self.team1_intel: entity.Flag = \
            await self.protocol.create_entity(entity.Flag, position=self.get_random_pos(team1), team=team1)
        self.team2_intel: entity.Flag = \
            await self.protocol.create_entity(entity.Flag, position=self.get_random_pos(team2), team=team2)
        self.team1_intel.on_collide += self.on_intel_collide
        self.team2_intel.on_collide += self.on_intel_collide
        self.intels = {self.team1_intel.team: self.team1_intel, self.team2_intel.team: self.team2_intel}

        self.team1_base: entity.Base = \
            await self.protocol.create_entity(entity.Base, position=self.get_random_pos(team1), team=team1)
        self.team2_base: entity.Base = \
            await self.protocol.create_entity(entity.Base, position=self.get_random_pos(team2), team=team2)
        self.team1_base.on_collide += self.on_base_collide
        self.team2_base.on_collide += self.on_base_collide
        self.bases = {self.team1_base.team: self.team1_base, self.team2_base.team: self.team2_base}

        self.pickup_sound = self.protocol.create_sound("pickup")
        self.capture_sound = self.protocol.create_sound("horn")

    async def on_intel_collide(self, intel: entity.Flag, player: 'connection.ServerConnection'):
        # print(intel, player)
        if intel.team == player.team:
            return

        await intel.set_carrier(player)
        await self.protocol.broadcast_hud_message(f"{player} picked up the {intel.team} Intel")
        await self.pickup_sound.play()

    async def on_base_collide(self, base: entity.Base, player: 'connection.ServerConnection'):
        # print(base, player)
        if base.team != player.team:
            return

        if self.protocol.time - player.store.get("ctf_last_restock", 0) >= 3:
            await player.restock()
            player.store["ctf_last_restock"] = self.protocol.time

        intel = self.intels[player.team.other]
        if intel.carrier == player:
            await intel.set_carrier(None)
            await intel.set_position(*self.get_random_pos(intel.team))
            await self.protocol.broadcast_hud_message(f"{player} captured the {intel.team} Intel")
            await self.capture_sound.play()

    def get_spawn_point(self, player: 'connection.ServerConnection') -> Tuple[int, int, int]:
        pos: Vector3 = self.team1_intel.position - Vector3(3, 3, 0)
        pos.z = self.protocol.map.get_z(pos.x, pos.y) - 2
        return pos.xyz
