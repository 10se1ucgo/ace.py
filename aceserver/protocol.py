import asyncio
import json
import textwrap
import os
import zlib
from contextlib import contextmanager
from typing import *

import enet

import acescripts
import acemodes
from acelib import packets, vxl, world
from acelib.bytes import ByteWriter
from acelib.constants import *
from aceserver import base, util, connection, types
from aceserver.loaders import *


class ServerProtocol(base.BaseProtocol):
    def __init__(self, config, *, loop):
        super().__init__(loop=loop, interface=config["interface"], port=config["port"],
                         connection_factory=connection.ServerConnection)

        self.config = config
        self.name = self.config["name"]
        self.max_players = min(32, self.config.get("max_players", 32))

        with open(self.config["map"], "rb") as f:
            self.map: vxl.VXLMap = vxl.VXLMap(f.read(), {"name": os.path.splitext(f.name)[0]})

        self.packs: List[Tuple[bytes, int, int]] = []
        for pname in self.config.get("packs", ()):
            with open(pname, "rb") as f:
                data = f.read()
                self.packs.append((data, len(data), zlib.crc32(data)))

        self.player_ids = util.IDPool(stop=self.max_players)
        # Client treats SetColor packets with player IDs >= 32 to be custom, server defined color data to store.
        # BlockAction then can use these player IDs for custom colors.
        self.color_ids = util.IDPool(start=32, stop=255)
        self.entity_ids = util.IDPool(stop=255)
        self.sound_ids = util.IDPool(stop=255)

        team1 = self.config.get("team1", {})
        team2 = self.config.get("team2", {})
        self.team1 = types.Team(self, TEAM.TEAM1, team1.get("name", "Blue"), team1.get("color", (44, 117, 179)))
        self.team2 = types.Team(self, TEAM.TEAM2, team2.get("name", "Green"), team2.get("color", (137, 179, 44)))
        self.spectator_team = types.Team(self, TEAM.SPECTATOR, "Spectator", (255, 255, 255), spectator=True)
        self.team1.other = self.team2
        self.team2.other = self.team1
        self.teams = {self.team1.id: self.team1, self.team2.id: self.team2, self.spectator_team.id: self.spectator_team}

        self.fog_color = self.config.get("fog_color", (128, 232, 255))

        self.players: Dict[int, connection.ServerConnection] = {}
        self.entities: Dict[int, types.Entity] = {}
        self.sounds: Dict[int, types.Sound] = {}
        self.objects: List[Any] = []

        self.mode: acemodes.GameMode = acemodes.get_game_mode(self, self.config.get("mode", "ctf"))
        self.scripts = acescripts.ScriptLoader(self)
        self.max_respawn_time = self.config.get("respawn_time", 5)

    async def run(self):
        self.init_hooks()
        await self.mode.init()
        self.scripts.load_scripts()
        await super().run()

    def stop(self):
        self.scripts.unload_scripts()
        print("Unloaded scripts")
        super().stop()

    def update(self, dt):
        super().update(dt)
        for ent in self.entities.values():
            ent.update(dt)
        for ply in self.players.values():
            ply.update(dt)
        for obj in self.objects:
            obj.update(dt)
        self.mode.update(dt)
        self.world_update()

    def world_update(self):
        world_update.clear()
        for conn in self.players.values():
            if not conn.name or conn.dead:
                continue
            world_update[conn.id] = (conn.position.xyz, conn.orientation)
        self._broadcast_loader(world_update.generate(), flags=enet.PACKET_FLAG_UNSEQUENCED)

    def _broadcast_loader(self, writer: ByteWriter, flags=enet.PACKET_FLAG_RELIABLE, predicate=None, connections=None):
        packet: enet.Packet = enet.Packet(bytes(writer), flags)

        if connections is not None:
            for conn in connections:
                conn.peer.send(0, packet)
            return

        if not callable(predicate):
            return self.host.broadcast(0, packet)

        for conn in self.connections.values():
            if predicate(conn):
                conn.peer.send(0, packet)

    def broadcast_loader(self, loader: packets.Loader, flags=enet.PACKET_FLAG_RELIABLE, *, predicate=None, connections=None):
        return self.loop.run_in_executor(None, self._broadcast_loader, loader.generate(), flags, predicate, connections)

    TObj = TypeVar('TObj')
    def create_object(self, obj_type: Type[TObj], *args, **kwargs) -> TObj:
        obj = obj_type(self, *args, **kwargs)
        self.objects.append(obj)
        return obj

    def destroy_object(self, obj):
        self.objects.remove(obj)

    TEnt = TypeVar('TEnt')
    async def create_entity(self, ent_type: Type[TEnt], *args, **kwargs) -> TEnt:
        ent = ent_type(self.entity_ids.pop(), self, *args, **kwargs)
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

    @contextmanager
    def block_color(self):
        id = self.color_ids.pop()
        yield id
        self.color_ids.push(id)

    @util.static_vars(wrapper=textwrap.TextWrapper(width=MAX_CHAT_SIZE))
    async def broadcast_message(self, message: str, chat_type=CHAT.SYSTEM, player_id=0xFF, predicate=None):
        chat_message.chat_type = chat_type
        chat_message.player_id = player_id
        lines: List[str] = self.broadcast_message.wrapper.wrap(message)
        for line in lines:
            chat_message.value = line
            await self.broadcast_loader(chat_message, predicate=predicate)

    def broadcast_chat_message(self, message: str, sender: connection.ServerConnection, team: types.Team=None):
        predicate = (lambda conn: conn.team == team) if team else None
        chat_type = CHAT.TEAM if team else CHAT.ALL
        return self.broadcast_message(message, player_id=sender.id, chat_type=chat_type, predicate=predicate)

    def broadcast_server_message(self, message: str, team: types.Team=None):
        predicate = (lambda conn: conn.team == team) if team else None
        return self.broadcast_message("[*] " + message, chat_type=CHAT.SYSTEM, predicate=predicate)

    def broadcast_hud_message(self, message: str, team: types.Team =None):
        predicate = (lambda conn: conn.team == team) if team else None
        return self.broadcast_message(message, chat_type=CHAT.BIG, predicate=predicate)

    def set_fog_color(self, r: int, g: int, b: int, save=True):
        r &= 255
        g &= 255
        b &= 255
        if save:
            self.fog_color = (r, g, b)
        fog_color.color.rgb = r, g, b
        return self.broadcast_loader(fog_color)

    async def player_joined(self, conn: 'connection.ServerConnection'):
        print(f"player join {conn.id}")
        self.players[conn.id] = conn

    async def player_left(self, conn: 'connection.ServerConnection'):
        print(f"player leave {conn.id}")
        ply = self.players.pop(conn.id, None)
        self.player_ids.push(conn.id)

        for ent in self.entities.values():
            if ent.carrier and ent.carrier.id == ply.id:
                await ent.set_carrier(None, force=True)

        if ply:  # PlayerLeft will crash the clients if the left player didn't actually join the game.
            player_left.player_id = conn.id
            await self.broadcast_loader(player_left)

    async def send_entity_carriers(self, conn: 'connection.ServerConnection'):
        """
        entities that already exist when a client connects (i.e. sent in StateData) have their
        carrier field ignored by the client; and you can't really patch it in client because as far as the
        client is aware no players exist by the time StateData is sent so it throws an error if you try to retrieve
        the player to set the carrier
        """
        for ent in self.entities.values():
            if ent.carrier is not None:
                await ent.set_carrier(ent.carrier, force=True)

    def get_state(self):
        state_data.fog_color.rgb = self.fog_color

        state_data.team1_color.rgb = self.team1.color
        state_data.team1_name = self.team1.name
        state_data.team1_score = self.team1.score

        state_data.team2_color.rgb = self.team2.color
        state_data.team2_name = self.team2.name
        state_data.team2_score = self.team2.score

        state_data.mode_name = self.mode.short_name
        state_data.score_limit = self.mode.score_limit

        state_data.entities = [ent.to_loader() for ent in self.entities.values()]
        return state_data

    def get_ply_by_name(self, name):
        for ply in self.players.values():
            if ply.name == name:
                return ply

    def get_respawn_time(self):
        offset = int(self.time % self.max_respawn_time)
        return self.max_respawn_time - offset

    def init_hooks(self):
        connection.ServerConnection.on_player_join += self.player_joined
        connection.ServerConnection.on_player_leave += self.player_left
        connection.ServerConnection.on_player_connect += self.send_entity_carriers

    def intercept(self, address: enet.Address, data: bytes):
        # Respond to server list query from client
        if data == b'HELLO':
            return self.host.socket.send(address, b'HI')
        elif data == b'HELLOLAN':
            entry = {
                "name": self.name, "players_current": len(self.players), "players_max": self.max_players,
                "map": self.map.name, "game_mode": self.mode.short_name, "game_version": "1.0a1"
            }
            payload = json.dumps(entry).encode()
            self.host.socket.send(address, payload)
