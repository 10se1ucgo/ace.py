from typing import Tuple

from aceserver import protocol, connection


class GameMode:
    name = "Default"
    score_limit = 0

    def __init__(self, protocol: 'protocol.ServerProtocol'):
        self.protocol = protocol

    async def init(self):
        pass

    async def update(self, dt: float):
        pass

    def get_spawn_point(self, player: 'connection.ServerConnection') -> Tuple[int, int, int]:
        return self.get_random_pos(player.team)

    def get_random_pos(self, team):
        offset = team.id * 384
        x, y, z = self.protocol.map.get_random_pos(0 + offset, 0, 128 + offset, 512)
        print(x, y, z)
        return x, y, z
