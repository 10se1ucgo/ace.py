import asyncio
import textwrap
import zlib
from typing import *

import enet

import acescripts
from acelib import packets, vxl, world
from acelib.bytes import ByteWriter
from acelib.constants import *
from acemodes import GameMode, ctf
from aceserver import base, util, connection, types
from aceserver.loaders import *


class ServerProtocol(base.BaseProtocol):
    def __init__(self, *args, **kwargs):
        super(ServerProtocol, self).__init__(*args, **kwargs, connection_factory=connection.ServerConnection)

        with open("normandie.vxl", "rb") as f:
            self.map: vxl.VXLMap = vxl.VXLMap(f.read())

        self.packs: List[Tuple[bytes, int, int]] = []
        for pname in ["packs/pack1.zip", "packs/pack2.zip"]:
            with open(pname, "rb") as f:
                data = f.read()
                self.packs.append((data, len(data), zlib.crc32(data)))

        self.player_ids = util.IDPool(stop=32)
        self.entity_ids = util.IDPool(stop=255)
        self.sound_ids = util.IDPool(stop=255)

        self.team1 = types.Team(TEAM.TEAM1, "Blue", (44, 117, 179), False, self)
        self.team2 = types.Team(TEAM.TEAM2, "Green", (137, 179, 44), False, self)
        self.team1.other = self.team2
        self.team2.other = self.team1
        self.teams = {self.team1.id: self.team1, self.team2.id: self.team2}

        self.players: Dict[int, connection.ServerConnection] = {}
        self.entities: Dict[int, types.Entity] = {}
        self.sounds: Dict[int, types.Sound] = {}
        self.world_objects = []

        # TODO: configs
        self.mode: GameMode = ctf.CTF(self)
        self.scripts = acescripts.ScriptLoader(self, {"scripts": ["commands", "censor"]})

    async def run(self):
        self.init_hooks()
        await self.mode.init()
        self.scripts.load_scripts()
        await super().run()

    def stop(self):
        self.scripts.unload_scripts()
        print("Unloaded scripts")
        super().stop()

    async def update(self, dt):
        await super().update(dt)
        ent_updates = [ent.update(dt) for ent in self.entities.values()]
        ply_updates = [ply.update(dt) for ply in self.players.values()]
        await asyncio.wait(ent_updates + ply_updates + [self.mode.update(dt)])
        await self.world_update()

    async def world_update(self):
        world_update.clear()
        for conn in self.players.values():
            if not conn.name:
                continue
            world_update[conn.id] = (conn.position.xyz, conn.orientation)
        await self.broadcast_loader(world_update, flags=enet.PACKET_FLAG_UNSEQUENCED)

    async def broadcast_loader(self, loader: packets.Loader, flags=enet.PACKET_FLAG_RELIABLE, *, predicate=None):
        writer: ByteWriter = loader.generate()
        packet: enet.Packet = enet.Packet(bytes(writer), flags)

        if not callable(predicate):
            return await self.loop.run_in_executor(None, self.host.broadcast, 0, packet)

        for conn in self.connections.values():
            if predicate(conn):
                await conn.send_loader(loader, flags)

    async def player_joined(self, conn: 'connection.ServerConnection'):
        print(f"player join {conn.id}")
        self.players[conn.id] = conn

    async def player_left(self, conn: 'connection.ServerConnection'):
        print(f"player leave {conn.id}")
        ply = self.players.pop(conn.id, None)
        self.player_ids.push(conn.id)
        if ply:  # PlayerLeft will crash the clients if the left player didn't actually join the game.
            player_left.player_id = conn.id
            await self.broadcast_loader(player_left)

    def create_world_object(self, obj_type, **kwargs):
        obj = obj_type(self.map)
        self.world_objects.append(obj)
        return obj

    def destroy_world_object(self, obj: world.WorldObject):
        self.world_objects.remove(obj)

    async def create_entity(self, ent_type: Type[types.Entity], **kwargs):
        ent = ent_type(self.entity_ids.pop(), self, **kwargs)
        self.entities[ent.id] = ent
        create_entity.entity = ent.to_loader()
        await self.broadcast_loader(create_entity)
        return ent

    async def destroy_entity(self, ent: types.Entity):
        destroy_entity.entity_id = ent.id
        await self.broadcast_loader(destroy_entity)
        self.entities.pop(ent.id)
        self.entity_ids.push(ent.id)

    def create_sound(self, name: str, position: tuple=None, looping: bool=False):
        sound_id = self.sound_ids.pop() if looping else None
        sound = types.Sound(self, sound_id, name, position)
        if looping:
            self.sounds[sound_id] = sound
        return sound

    def destroy_sound(self, sound: types.Sound):
        if sound.id is not None:
            self.sounds.pop(sound.id)
            self.sound_ids.push(sound.id)

    @util.static_vars(wrapper=textwrap.TextWrapper(width=MAX_CHAT_SIZE))
    async def broadcast_message(self, message: str, chat_type=CHAT.SYSTEM, player_id=0xFF, predicate=None):
        chat_message.chat_type = chat_type
        chat_message.player_id = player_id
        lines: List[str] = self.broadcast_message.wrapper.wrap(message)
        for line in lines:
            chat_message.value = line
            await self.broadcast_loader(chat_message, predicate=predicate)

    def broadcast_chat_message(self, message: str, sender: connection.ServerConnection, team: types.Team =None):
        predicate = (lambda conn: conn.team == team) if team else None
        chat_type = CHAT.TEAM if team else CHAT.ALL
        return self.broadcast_message(message, player_id=sender.id, chat_type=chat_type, predicate=predicate)

    def broadcast_server_message(self, message: str, team: types.Team =None):
        predicate = (lambda conn: conn.team == team) if team else None
        return self.broadcast_message(message, chat_type=CHAT.BIG, predicate=predicate)

    def broadcast_hud_message(self, message: str, team: types.Team =None):
        predicate = (lambda conn: conn.team == team) if team else None
        return self.broadcast_message(message, chat_type=CHAT.BIG, predicate=predicate)

    def get_state(self):
        state_data.fog_color.rgb = (0, 0, 0)

        state_data.team1_color.rgb = self.team1.color
        state_data.team1_name = self.team1.name
        state_data.team1_score = self.team1.score

        state_data.team2_color.rgb = self.team2.color
        state_data.team2_name = self.team2.name
        state_data.team2_score = self.team2.score

        state_data.mode_name = self.mode.name
        state_data.score_limit = self.mode.score_limit

        state_data.entities = [ent.to_loader() for ent in self.entities.values()]
        return state_data

    def init_hooks(self):
        connection.ServerConnection.on_player_join += self.player_joined
        connection.ServerConnection.on_player_leave += self.player_left
