from acelib.constants import KILL
from acemodes import GameMode
from aceserver import types
from aceserver.protocol import ServerProtocol
from aceserver.connection import ServerConnection


class CTF(GameMode):
    name = "CTF"
    score_limit = 10

    async def init(self):
        await super().init()

        team1 = self.protocol.team1
        team2 = self.protocol.team2

        self.team1_intel = \
            await self.protocol.create_entity(types.Flag, position=self.get_random_pos(team1), team=team1)
        self.team2_intel = \
            await self.protocol.create_entity(types.Flag, position=self.get_random_pos(team2), team=team2)
        self.intels = {self.team1_intel.team: self.team1_intel, self.team2_intel.team: self.team2_intel}
        types.Flag.on_collide += self.on_intel_collide

        self.team1_cp = \
            await self.protocol.create_entity(types.CommandPost, position=self.get_random_pos(team1), team=team1)
        self.team2_cp = \
            await self.protocol.create_entity(types.CommandPost, position=self.get_random_pos(team2), team=team2)
        self.cps = {self.team1_cp.team: self.team1_cp, self.team2_cp.team: self.team2_cp}
        types.CommandPost.on_collide += self.on_cp_collide

        self.pickup_sound = self.protocol.create_sound("pickup")

        # self.crate_sound = self.protocol.create_sound("chopper")
        # self.crate_spawner_task = self.protocol.loop.create_task(self.spawn_crates())

    async def deinit(self):
        [intel.destroy() for intel in self.intels.values()]
        [cp.destroy() for cp in self.cps.values()]

    # async def spawn_crates(self):
    #     while True:
    #         crate_type = random.choice((types.AmmoCrate, types.HealthCrate))
    #         pos = self.protocol.map.get_random_pos(0, 0, 512, 512)
    #         print(f"Spawning crate at {pos}")
    #         self.crate_sound.position = pos
    #         await self.crate_sound.play()
    #         await self.protocol.create_entity(ent_type=crate_type, position=pos, team=None)
    #         await asyncio.sleep(10)

    async def on_intel_collide(self, intel: types.Flag, player: ServerConnection):
        if intel.team == player.team:
            return

        await intel.set_carrier(player)
        await self.protocol.broadcast_hud_message(f"{player} picked up the {intel.team} Intel")
        await self.pickup_sound.play()

    async def on_cp_collide(self, base: types.CommandPost, player: ServerConnection):
        if base.team != player.team:
            return

        if self.protocol.time - player.store.get("ctf_last_restock", 0) >= 3:
            await player.restock()
            player.store["ctf_last_restock"] = self.protocol.time

        intel = self.intels[player.team.other]
        if intel.carrier == player:
            await self.capture_intel(player, intel)

    async def capture_intel(self, player: ServerConnection, intel: types.Flag):
        await self.reset_intel(intel)
        player.team.score += 1
        player.score += 10
        await self.protocol.broadcast_hud_message(f"{player} captured the {intel.team} Intel")
        self.check_win()

    async def drop_intel(self, player: ServerConnection, intel: types.Flag):
        await intel.set_carrier(None)
        await intel.set_position(*player.position.xyz)
        await self.protocol.broadcast_hud_message(f"{player} dropped the {intel.team} Intel")

    async def reset_intel(self, intel):
        await intel.set_carrier(None)
        await intel.set_position(*self.get_random_pos(intel.team))

    async def on_player_kill(self, player: ServerConnection, kill_type: KILL, killer: ServerConnection):
        await super().on_player_kill(player, kill_type, killer)
        intel = self.intels[player.team.other]
        if intel.carrier == player:
            await self.drop_intel(player, intel)


def init(protocol: ServerProtocol):
    return CTF(protocol)
