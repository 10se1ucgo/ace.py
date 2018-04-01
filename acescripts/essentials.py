"""
The (eventually) default set of commands

Creator: 10se1ucgo
"""
import asyncio
import inspect

from acelib.world import cast_ray
from aceserver import types
from aceserver.protocol import ServerProtocol
from aceserver.connection import ServerConnection
from acescripts import Script, commands


class EssentialsScript(Script):
    @commands.command(admin=True)
    def setpos(self, connection: ServerConnection, x: float, y: float, z: float=None):
        connection.set_position(x, y, z)

    @commands.command(admin=True)
    def sethp(self, connection: ServerConnection, hp: int):
        connection.set_hp(hp)

    @commands.command(admin=True)
    def hurt(self, connection: ServerConnection, hp: int):
        connection.hurt(hp)

    @commands.command(admin=True)
    def tp(self, connection: ServerConnection, other: ServerConnection):
        connection.set_position(*other.position.xyz)

    @commands.command(admin=True)
    def goto(self, connection: ServerConnection, grid_pos: str):
        x, y = self.protocol.map.from_grid(grid_pos)
        connection.set_position(x, y)

    @commands.command(admin=True)
    def spawn(self, connection: ServerConnection, type: types.Entity, num: int=1, x: float=None, y: float=None, z: float=None):
        for j in range(num):
            if x is None or y is None:
                pos = connection.protocol.mode.get_random_pos(connection.team)
            else:
                if z is None:
                    z = self.protocol.map.get_z(x, y)
                pos = (x, y, z)
            self.protocol.create_entity(ent_type=type, position=pos, team=connection.team)

    @commands.command(admin=True)
    def cast(self, connection: ServerConnection):
        self.protocol.loop.create_task(self.test32(connection))

    async def test32(self, connection: ServerConnection):
        while True:
            print("yo")
            pos = cast_ray(connection.protocol.map, connection.position, connection.orientation, length=256)
            if not pos:
                break
            connection.protocol.destroy_block(*pos)
            await asyncio.sleep(1 / 10)

    @commands.command(admin=True)
    def grenade(self, connection: ServerConnection, x: float, y: float, z: float, a: float=0, b: float=0, c: float=0):
        obj = self.protocol.create_object(types.Grenade, connection, (x, y, z), (a, b, c))
        eta, pos = obj.next_collision(dt=1/60, max=20)
        if eta is not False:
            obj.fuse = eta
        obj.broadcast_item()

    @commands.command(admin=True)
    def fog(self, connection: ServerConnection, r: int, g: int, b: int):
        self.protocol.set_fog_color(r, g, b)


def init(protocol: ServerProtocol):
    return EssentialsScript(protocol)
