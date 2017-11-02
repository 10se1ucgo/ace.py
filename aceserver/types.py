from aceserver import protocol
from aceserver.loaders import play_sound, stop_sound


class Sound:
    def __init__(self, protocol: 'protocol.ServerProtocol', loop_id: int, name: str, position: tuple=None):
        self.protocol = protocol

        self.id = loop_id
        self.name = name
        self.position = position

    async def play(self, predicate=None):
        play_sound.name = self.name
        play_sound.looping = self.id is not None
        play_sound.loop_id = self.id or 0
        play_sound.positioned = self.position is not None
        play_sound.position.xyz = self.position or (0, 0, 0)
        await self.protocol.broadcast_loader(play_sound, predicate=predicate)

    async def stop(self, predicate=None):
        if self.id is None:
            return
        stop_sound.loop_id = self.id
        await self.protocol.broadcast_loader(stop_sound, predicate=predicate)

    async def destroy(self):
        await self.stop()
        self.protocol.destroy_sound(self)
