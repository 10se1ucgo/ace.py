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

    async def reset(self):
        pass

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
        x, y ,z = self.get_random_pos(player.team)
        return x, y, z - 2

    def get_random_pos(self, team):
        offset = team.id * 384
        x, y, z = self.protocol.map.get_random_pos(0 + offset, 0, 128 + offset, 512)
        print(x, y, z)
        return x, y, z
