import asyncio
from typing import Tuple

from acelib import constants
from aceserver import protocol, connection, types


FOG_COLORS = ((251,  76,   0),
              (119, 215, 118),
              ( 37,  78, 235),
              (222, 209,   2),
              (224, 113, 234),
              (255, 255, 255))


class GameMode:
    name = "Default"
    score_limit = 0

    def __init__(self, protocol: 'protocol.ServerProtocol'):
        self.protocol = protocol

    async def init(self):
        # TODO should this be in the base GameMode or should this just be default behaviour within these classes?
        types.HealthCrate.on_collide += self.on_health_crate
        types.AmmoCrate.on_collide += self.on_ammo_crate
        connection.ServerConnection.on_player_kill += self.on_player_kill

        self.win_sound = self.protocol.create_sound("horn")

    async def deinit(self):
        pass

    async def reset(self, winner: types.Team=None):
        if winner is not None:
            self.protocol.loop.create_task(self.celebrate())
            await self.protocol.broadcast_hud_message(f"{winner.name} team wins!")
        await self.deinit()
        await self.init()
        for player in self.protocol.players.values():
            await player.spawn()
        for team in self.protocol.teams.values():
            team.reset()

    def check_win(self):
        if any(team.score == self.score_limit for team in self.protocol.teams.values()):
            winner = max(self.protocol.teams.values(), key=lambda team: team.score)
            self.protocol.loop.create_task(self.reset(winner))


    def update(self, dt: float):
        pass

    async def on_health_crate(self, crate: types.HealthCrate, connection: 'connection.ServerConnection'):
        await connection.set_hp(100)
        crate.destroy()

    async def on_ammo_crate(self, crate: types.AmmoCrate, connection: 'connection.ServerConnection'):
        connection.weapon.restock()
        await connection.weapon.send_ammo()
        crate.destroy()

    async def on_player_kill(self, player: 'connection.ServerConnection', kill_type: constants.KILL, killer: 'connection.ServerConnection'):
        if killer is player:
            # suicide
            killer.score -= 1
        else:
            killer.score += 1

    def get_spawn_point(self, player: 'connection.ServerConnection') -> Tuple[int, int, int]:
        x, y, z = self.get_random_pos(player.team)
        return x + 0.5, y + 0.5, z - 2

    def get_random_pos(self, team):
        sections = self.protocol.map.width() / 8
        offset = team.id * (self.protocol.map.width() - (sections * 2))
        x, y, z = self.protocol.map.get_random_pos(0 + offset, 0, (sections * 2) + offset, self.protocol.map.width())
        return x, y, z

    async def celebrate(self):
        await self.win_sound.play()
        original = self.protocol.fog_color
        for x in range(3):
            for color in FOG_COLORS:
                await self.protocol.set_fog_color(*color, save=False)
                await asyncio.sleep(1/3)
        await self.protocol.set_fog_color(*original)
