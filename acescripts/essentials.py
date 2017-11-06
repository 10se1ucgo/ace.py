"""
The (eventually) default set of commands

Creator: 10se1ucgo
"""
from aceserver.protocol import ServerProtocol
from aceserver.connection import ServerConnection
from acescripts import Script, commands


class EssentialsScript(Script):
    def __init__(self, protocol: ServerProtocol, cfg: dict):
        self.protocol = protocol
        # TODO is this the best way to add commands?
        # Perhaps the commands script should check each script for commands by itself.
        self.protocol.scripts.get("commands").add_commands(self)

    def deinit(self):
        self.protocol.scripts.get("commands").remove_commands(self)

    @commands.command()
    async def setpos(self, connection: ServerConnection, x: float, y: float, z: float=None):
        await connection.set_position(x, y, z)

    @commands.command()
    async def sethp(self, connection: ServerConnection, hp: int):
        await connection.set_hp(hp)

    @commands.command()
    async def hurt(self, connection: ServerConnection, hp: int):
        await connection.hurt(hp)

    @commands.command()
    async def tp(self, connection: ServerConnection, other: ServerConnection):
        await connection.set_position(*other.position.xyz)


def init(protocol: ServerProtocol, cfg: dict):
    return EssentialsScript(protocol, cfg)
