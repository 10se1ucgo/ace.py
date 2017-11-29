"""
Greetiing script

Creator: 10se1ucgo
"""
from aceserver.protocol import ServerProtocol
from aceserver.connection import ServerConnection
from acescripts import Script


class GreetingScript(Script):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.intro_sound = self.protocol.create_sound("intro")
        # TODO find a cleaner way to have this
        ServerConnection.on_player_connect += self.intro
        ServerConnection.on_player_join += self.greet

    async def intro(self, connection: ServerConnection):
        await connection.play_sound(self.intro_sound)

    async def greet(self, connection: ServerConnection):
        await connection.send_hud_message(f"Welcome to the server, {connection.name}!")
        await self.protocol.broadcast_message(f"{connection.name} has joined the server.")


def init(protocol: ServerProtocol):
    return GreetingScript(protocol)
