from typing import Tuple

from aceserver import protocol, connection, types


async def _on_healthcrate(crate: types.HealthCrate, connection: 'connection.ServerConnection'):
    await connection.set_hp(100)
    await crate.destroy()


async def _on_ammocrate(crate: types.AmmoCrate, connection: 'connection.ServerConnection'):
    connection.weapon.restock()
    await connection.weapon.send_ammo()
    await crate.destroy()


class GameMode:
    name = "Default"
    score_limit = 0

    def __init__(self, protocol: 'protocol.ServerProtocol'):
        self.protocol = protocol

    async def init(self):
        # TODO should this be in the base GameMode or should this just be default behaviour within the Health/AmmoCrate class?
        types.HealthCrate.on_collide += _on_healthcrate
        types.AmmoCrate.on_collide += _on_ammocrate

    async def deinit(self):
        pass

    async def update(self, dt: float):
        pass

    def get_spawn_point(self, player: 'connection.ServerConnection') -> Tuple[int, int, int]:
        x, y ,z = self.get_random_pos(player.team)
        return x, y, z - 2

    def get_random_pos(self, team):
        offset = team.id * 384
        x, y, z = self.protocol.map.get_random_pos(0 + offset, 0, 128 + offset, 512)
        print(x, y, z)
        return x, y, z
