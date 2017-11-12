from typing import Generator

from acelib import math3d, packets, world
from acelib.constants import TEAM, SET, ENTITY, SCORE, KILL, ACTION
from aceserver import protocol, connection, util, loaders
from aceserver.loaders import play_sound, stop_sound, change_entity, grenade_packet


class Sound:
    def __init__(self, protocol: 'protocol.ServerProtocol', loop_id: int, name: str, position: tuple=None):
        self.protocol = protocol

        self.id = loop_id
        self.name = name
        self.position = position

    async def play(self, predicate=None):
        await self.protocol.broadcast_loader(self.to_play_sound(), predicate=predicate)

    async def stop(self, predicate=None):
        if self.id is None:
            return
        stop_sound.loop_id = self.id
        await self.protocol.broadcast_loader(stop_sound, predicate=predicate)

    async def destroy(self):
        await self.stop()
        self.protocol.destroy_sound(self)

    def to_play_sound(self):
        play_sound.name = self.name
        play_sound.looping = self.id is not None
        play_sound.loop_id = self.id or 0
        play_sound.positioned = self.position is not None
        play_sound.position.xyz = self.position or (0, 0, 0)
        return play_sound

class Team(object):
    def __init__(self, team_id: TEAM, name: str, color: tuple, spectator: bool, protocol: 'protocol.ServerProtocol'):
        self.id = team_id
        self.name = name
        self.color = color
        self.spectator = spectator
        self.protocol = protocol

        self.other: 'Team' = None

        self.score = 0
        self.kills = 0

    def players(self) -> Generator['connection.ServerConnection', None, None]:
        for conn in self.protocol.players.values():
            if conn.player.team == self:
                yield conn

    def entities(self) -> Generator['Entity', None, None]:
        for ent in self.protocol.entities.values():
            if ent.team == self:
                yield ent

    async def set_score(self, new_score=None):
        if new_score is not None:
            self.score = new_score
        loaders.set_score.type = SCORE.TEAM
        loaders.set_score.specifier = self.id
        loaders.set_score.value = self.score
        await self.protocol.broadcast_loader(loaders.set_score)

    def broadcast_chat_message(self, message: str, sender: 'connection.ServerConnection'):
        return self.protocol.broadcast_chat_message(message, sender, team=self)

    def broadcast_server_message(self, message: str):
        return self.protocol.broadcast_server_message(message, team=self)

    def broadcast_hud_message(self, message: str):
        return self.protocol.broadcast_hud_message(message, team=self)

    def __str__(self):
        return f"{self.name} team"

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id!r}, name={self.name}, color={self.color})>"


class Entity:
    type = None
    mountable = False
    on_collide = util.AsyncEvent()

    def __init__(self, entity_id: int, protocol: 'protocol.ServerProtocol', **kwargs):
        self.id = entity_id
        self.protocol = protocol

        self.position = math3d.Vector3(*kwargs.get("position", (0, 0, 0)))
        self.team: Team = kwargs.get("team")
        self.carrier: connection.ServerConnection = kwargs.get("carrier")

        self.destroyed = False

    async def update(self, dt):
        if self.destroyed:
            return

        z = self.protocol.map.get_z(self.position.x, self.position.y, self.position.z - 1)
        if z != self.position.z:
            await self.set_position(self.position.x, self.position.y, z)

        if not self.carrier:
            for conn in self.protocol.players.values():
                dist = self.position.sq_distance(conn.position)
                if dist <= 3 ** 2:
                    self.protocol.loop.create_task(self.on_collide(self, conn))

    async def set_team(self, team):
        if self.destroyed:
            return
        self.team = team
        state = self.team.id if self.team else TEAM.NEUTRAL
        change_entity.entity_id = self.id
        change_entity.type = SET.STATE
        change_entity.state = state
        await self.protocol.broadcast_loader(change_entity)

    async def set_position(self, x, y, z):
        if self.destroyed:
            return
        self.position.xyz = x, y, z
        change_entity.entity_id = self.id
        change_entity.type = SET.POSITION
        change_entity.position.xyz = self.position.xyz
        await self.protocol.broadcast_loader(change_entity)

    async def set_carrier(self, carrier=None):
        if self.destroyed:
            return
        self.carrier = carrier
        player = self.carrier.id if self.carrier else -1
        change_entity.entity_id = self.id
        change_entity.type = SET.CARRIER
        change_entity.carrier = player
        await self.protocol.broadcast_loader(change_entity)

    async def destroy(self):
        if self.destroyed:
            return
        await self.protocol.destroy_entity(self)
        self.destroyed = True

    def to_loader(self):
        if self.destroyed:
            return
        ent = packets.Entity()
        ent.position.xyz = self.position.xyz
        ent.id = self.id
        ent.type = self.type
        ent.carrier = -1 if self.carrier is None else self.carrier.id
        ent.state = TEAM.NEUTRAL if self.team is None else self.team.id
        return ent

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return f"<Entity(id={self.id}, type={self.type!r}, pos={self.position})>"


class Flag(Entity):
    type = ENTITY.FLAG
    on_collide = util.AsyncEvent()


class Helicopter(Entity):
    type = ENTITY.HELICOPTER
    on_collide = util.AsyncEvent()


class AmmoCrate(Entity):
    type = ENTITY.AMMO_CRATE
    on_collide = util.AsyncEvent()


class HealthCrate(Entity):
    type = ENTITY.HEALTH_CRATE
    on_collide = util.AsyncEvent()


class CommandPost(Entity):
    type = ENTITY.COMMAND_POST
    on_collide = util.AsyncEvent()


class Grenade:
    on_throw = util.AsyncEvent()
    on_collide = util.AsyncEvent()
    on_explode = util.AsyncEvent()

    def __init__(self, protocol: 'protocol.ServerProtocol', thrower: 'connection.ServerConnection', fuse, position, velocity):
        self.protocol = protocol
        self.thrower = thrower
        self.wo = world.Grenade(protocol.map, *position, *velocity)
        self.explode_time = self.protocol.time + fuse
        self.protocol.loop.create_task(self.on_throw(self))

    async def update(self, dt):
        bounced = self.wo.update(dt, self.protocol.time)
        if bounced:
            self.protocol.loop.create_task(self.on_collide(self))
        if self.protocol.time >= self.explode_time:
            await self.explode()
            self.protocol.destroy_object(self)

    async def explode(self):
        x, y, z = self.wo.position.xyz
        await self.thrower.destroy_block(int(x), int(y), int(z), ACTION.GRENADE)
        for player in self.protocol.players.values():
            dist = player.position.sq_distance(self.wo.position)
            if dist < 16 ** 2 and self.hit_test(player):
                if dist == 0:
                    damage = 100
                else:
                    damage = 4096 / dist
                await player.hurt(damage, KILL.GRENADE, self.thrower)
        self.protocol.loop.create_task(self.on_explode(self))

    async def broadcast_grenade(self, predicate=None):
        grenade_packet.player_id = self.thrower.id
        grenade_packet.value = self.explode_time - self.protocol.time
        grenade_packet.position.xyz = self.wo.position.xyz
        grenade_packet.velocity.xyz = self.wo.velocity.xyz
        await self.protocol.broadcast_loader(grenade_packet, predicate=predicate)

    def hit_test(self, player: 'connection.ServerConnection'):
        return not world.cast_ray(self.protocol.map, player.position, self.wo.position, isdirection=False)
