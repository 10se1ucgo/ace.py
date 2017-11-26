from typing import Tuple

from acelib import constants
from aceserver import protocol, connection, types


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

    async def deinit(self):
        pass

    async def reset(self, winner: types.Team=None):
        pass

    def check_win(self):
        team1 = self.protocol.team1
        team2 = self.protocol.team2
        if team1.score == self.score_limit or team2.score == self.score_limit:
            winner = team1 if team1.score > team2.score else team2
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
