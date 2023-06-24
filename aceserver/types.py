import math
from typing import Generator

from acelib import math3d, packets, world
from acelib.constants import TEAM, SET, ENTITY, SCORE, KILL, ACTION, ROCKET_SPEED, ROCKET_FALLOFF, TOOL
from aceserver import protocol, connection, util, loaders
from aceserver.loaders import play_sound, stop_sound, change_entity, oriented_item


class Sound:
    def __init__(self, protocol: 'protocol.ServerProtocol', loop_id: int, name: str, position: tuple=None):
        self.protocol = protocol

        self.id = loop_id
        self.name = name
        self.position = position

    def play(self, predicate=None):
        self.protocol.broadcast_loader(self.to_play_sound(), predicate=predicate)

    def stop(self, predicate=None):
        if self.id is None:
            return
        stop_sound.loop_id = self.id
        self.protocol.broadcast_loader(stop_sound, predicate=predicate)

    def destroy(self):
        self.stop()
        self.protocol.destroy_sound(self)

    def to_play_sound(self):
        play_sound.name = self.name
        play_sound.looping = self.id is not None
        play_sound.loop_id = self.id or 0
        play_sound.positioned = self.position is not None
        play_sound.position.xyz = self.position or (0, 0, 0)
        return play_sound


class Team:
    def __init__(self, protocol: 'protocol.ServerProtocol', team_id: TEAM, name: str, color: tuple, spectator: bool=False):
        self.protocol = protocol
        self.id = team_id
        self.name = name
        self.color = color
        self.spectator = spectator

        self.other: 'Team' = None

        self._score = 0

    def players(self) -> Generator['connection.ServerConnection', None, None]:
        for conn in self.protocol.players.values():
            if conn.team is self:
                yield conn

    def entities(self) -> Generator['Entity', None, None]:
        for ent in self.protocol.entities.values():
            if ent.team is self:
                yield ent

    def reset(self):
        self.score = 0

    def broadcast_chat_message(self, message: str, sender: 'connection.ServerConnection'):
        return self.protocol.broadcast_chat_message(message, sender, team=self)

    def broadcast_server_message(self, message: str):
        return self.protocol.broadcast_server_message(message, team=self)

    def broadcast_hud_message(self, message: str):
        return self.protocol.broadcast_hud_message(message, team=self)

    @property
    def score(self):
        return self._score

    @score.setter
    def score(self, value):
        self._score = value
        loaders.set_score.type = SCORE.TEAM
        loaders.set_score.specifier = self.id
        loaders.set_score.value = self._score
        self.protocol.broadcast_loader(loaders.set_score)

    def __str__(self):
        return f"{self.name} team"

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id!r}, name={self.name}, color={self.color})>"


class Entity:
    type = None
    mountable = False
    on_collide = util.Event()

    def __init__(self, entity_id: int, protocol: 'protocol.ServerProtocol', position=(0, 0, 0), team=None, carrier=None,
                 yaw: float=0.0):
        self.id = entity_id
        self.protocol = protocol

        self.position = math3d.Vector3(*position)
        self.yaw = yaw
        self.team: Team = team
        self.carrier: connection.ServerConnection = carrier

        self.destroyed = False

    def update(self, dt):
        if self.destroyed:
            return

        self.do_gravity()
        self.do_collide()

    def do_gravity(self):
        z = self.protocol.map.get_z(self.position.x, self.position.y, self.position.z - 1)
        if z != self.position.z:
            self.set_position(self.position.x, self.position.y, z)

    def do_collide(self):
        if not self.carrier and self.on_collide:
            for conn in self.protocol.players.values():
                if conn.dead: continue

                dist = self.position.sq_distance(conn.position)
                if dist <= 3 ** 2:
                    self.on_collide(self, conn)

    def set_team(self, team: Team=None, force=False):
        if self.destroyed:
            return
        if not force and team is self.team:
            return
        self.team = team
        state = self.team.id if self.team else TEAM.NEUTRAL
        change_entity.entity_id = self.id
        change_entity.type = SET.STATE
        change_entity.state = state
        self.protocol.broadcast_loader(change_entity)

    def set_position(self, x: float, y: float, z: float):
        if self.destroyed:
            return
        self.position.set(x, y, z)
        change_entity.entity_id = self.id
        change_entity.type = SET.POSITION
        change_entity.position.xyz = self.position.xyz
        self.protocol.broadcast_loader(change_entity)

    def set_carrier(self, carrier: 'connection.ServerConnection'=None, force=False):
        if self.destroyed:
            return
        if not force and carrier is self.carrier:
            return
        self.carrier = carrier
        player = self.carrier.id if self.carrier else -1
        change_entity.entity_id = self.id
        change_entity.type = SET.CARRIER
        change_entity.carrier = player
        self.protocol.broadcast_loader(change_entity)

    def destroy(self):
        if self.destroyed:
            return
        self.destroyed = True
        self.protocol.destroy_entity(self)

    def to_loader(self):
        if self.destroyed:
            return
        ent = packets.Entity()
        ent.position.xyz = self.position.xyz
        ent.yaw = self.yaw
        ent.id = self.id
        ent.type = self.type
        ent.carrier = -1 if self.carrier is None else self.carrier.id
        ent.state = TEAM.NEUTRAL if self.team is None else self.team.id
        return ent

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return f"<Ent.{self.__class__.__name__}(id={self.id}, type={self.type!r}, pos={self.position})>"


class Flag(Entity):
    type = ENTITY.FLAG
    on_collide = util.Event()


class CommandPost(Entity):
    type = ENTITY.COMMAND_POST
    on_collide = util.Event()


class Helicopter(Entity):
    type = ENTITY.HELICOPTER
    on_collide = util.Event()


class AmmoCrate(Entity):
    type = ENTITY.AMMO_CRATE
    on_collide = util.Event()


class HealthCrate(Entity):
    type = ENTITY.HEALTH_CRATE
    on_collide = util.Event()


class MountableEntity(Entity):
    mountable = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        connection.ServerConnection.on_use_command += self.try_mount
        connection.ServerConnection.on_walk_change += self.player_walk
        connection.ServerConnection.on_animation_change += self.player_animation

    async def try_mount(self, connection: 'connection.ServerConnection'):
        if self.carrier is not None:
            if connection is self.carrier:
                self.mount(None)
            else:
                return
        elif connection.position.sq_distance(self.position) <= 3 ** 2:
            self.mount(connection)

    def mount(self, connection):
        if connection is None:
            self.carrier.mounted_entity = None
        else:
            connection.mounted_entity = self
        self.set_carrier(connection)

    async def player_walk(self, connection, forward: bool, backward: bool, left: bool, right: bool):
        pass

    async def player_animation(self, connection, jump: bool, crouch: bool, sneak: bool, sprint: bool):
        pass


class MachineGun(MountableEntity):
    type = ENTITY.MACHINE_GUN

    MG_SHOOT_RATE = 0.2

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_fire = 0

    async def player_walk(self, connection, *args):
        if connection is self.carrier and any(args):
            self.mount(None)

    async def player_animation(self, connection, *args):
        if connection is self.carrier and any(args):
            self.mount(None)

    def check_rapid(self):
        # if self.protocol.time - self.last_fire < (self.MG_SHOOT_RATE - 0.025):
        #     return False
        # self.last_fire = self.protocol.time
        return True

    def get_damage(self, value, dist):
        return 10



ENTITIES = {cls.type: cls for cls in Entity.__subclasses__() if cls.type is not None and cls.type in ENTITY}


class Explosive:
    on_throw = util.AsyncEvent()
    on_explode = util.AsyncEvent()

    def __init__(self, protocol, world_object, thrower):
        self.protocol = protocol
        self.wo = world_object
        self.thrower = thrower
        self.destroyed = False
        self.protocol.loop.create_task(self.on_throw(self))

    def update(self, dt):
        pass

    def explode(self):
        self.destroy()

        x, y, z = self.wo.position.xyz
        self.thrower.destroy_block(int(x), int(y), int(z), ACTION.GRENADE)
        for player in self.protocol.players.values():
            if player.dead: continue

            dist = player.position.sq_distance(self.wo.position)
            if dist < 16 ** 2 and self.hit_test(player):
                if dist == 0:
                    damage = 100
                else:
                    damage = 4096 / dist
                player.hurt(damage, KILL.GRENADE, self.thrower, self.position.xyz)
        self.protocol.loop.create_task(self.on_explode(self))

    def broadcast_item(self, predicate=None):
        raise NotImplementedError

    def hit_test(self, player: 'connection.ServerConnection'):
        return not world.cast_ray(self.protocol.map, player.position, self.wo.position, isdirection=False)

    def destroy(self):
        self.destroyed = True
        self.protocol.destroy_object(self)

    @property
    def position(self) -> math3d.Vector3:
        return self.wo.position


class Grenade(Explosive):
    on_throw = util.AsyncEvent()
    on_collide = util.AsyncEvent()
    on_explode = util.AsyncEvent()

    def __init__(self, protocol: 'protocol.ServerProtocol', thrower: 'connection.ServerConnection', position, velocity, fuse=5):
        self.wo = world.Grenade(protocol.map, *position, *velocity)
        super().__init__(protocol, self.wo, thrower)

        self.start_time = self.protocol.time
        self.explode_time = self.start_time + fuse

    def update(self, dt):
        if self.destroyed: return

        bounced = self.wo.update(dt, self.protocol.time)
        if bounced:
            self.protocol.loop.create_task(self.on_collide(self))
        if self.protocol.time >= self.explode_time:
            self.explode()

    def next_collision(self, dt: float, max: float=5):
        return self.wo.next_collision(dt, max)

    def broadcast_item(self, predicate=None):
        oriented_item.player_id = self.thrower.id
        oriented_item.value = self.fuse
        oriented_item.position.xyz = self.wo.position.xyz
        oriented_item.velocity.xyz = self.wo.velocity.xyz
        oriented_item.tool = TOOL.GRENADE
        self.protocol.broadcast_loader(oriented_item, predicate=predicate)

    @property
    def fuse(self):
        return self.explode_time - self.protocol.time

    @fuse.setter
    def fuse(self, value):
        self.explode_time = self.start_time + value


class Rocket(Explosive):
    on_throw = util.AsyncEvent()
    on_explode = util.AsyncEvent()

    def __init__(self, protocol: 'protocol.ServerProtocol', thrower: 'connection.ServerConnection', position, orientation, value=None):
        self.wo = world.GenericMovement(protocol.map, *position)
        super().__init__(protocol, self.wo, thrower)

        # i dont know math so im going to try my best to replicate the client
        self.pitch = self.yaw = 0
        self.yawmat = None
        self.set_orientation(*orientation)

    def update(self, dt):
        if self.destroyed: return

        b = math3d.Matrix4x4.rotate(self.pitch, math3d.Vector3(-1, 0, 0))
        rotation = b * self.yawmat

        # im not sure if the error is in my Matrix class or mat's, but mat4 * vec3 behaves differently
        # his implementation seems to multiply each matrix column by the vector, not each row, which is how i learned it
        # so instead of doing the proper thing (velocity = rotation * vec3(0, 0, -1)) we'll just emulate his version
        velocity = tuple(x for x in rotation.get_row(2)[:3])
        velocity = math3d.Vector3(-velocity[0], -velocity[2], velocity[1])

        f = dt * ROCKET_SPEED
        self.wo.position += velocity * f

        bounced = self.wo.update(dt, self.protocol.time)
        if bounced:
            self.explode()

        self.pitch += math.radians(ROCKET_FALLOFF) * dt

    def set_orientation(self, x: int, y: int, z: int):
        try:
            self.pitch = math.asin(z)
        except ValueError:
            self.pitch = math.pi / 2

        try:
            self.yaw = math.atan2(x, y)
        except ValueError:
            self.yaw = 0.0

        self.yawmat = math3d.Matrix4x4.rotate(self.yaw + math.pi, math3d.Vector3(0, 1, 0))

    def get_orientation(self) -> (int, int, int):
        x = math.sin(self.yaw) * math.cos(self.pitch)
        y = math.cos(self.yaw) * math.cos(self.pitch)
        z = math.sin(self.pitch)
        return (x, y, z)

    # a1 client is bork, assumes all UseOrientedItem packets are grenades.
    # (this is fixed in later builds)
    def broadcast_item(self, predicate=None):
        oriented_item.player_id = self.thrower.id
        oriented_item.value = 0
        oriented_item.position.xyz = self.wo.position.xyz
        oriented_item.velocity.xyz = self.get_orientation()
        oriented_item.tool = TOOL.RPG
        self.protocol.broadcast_loader(oriented_item, predicate=predicate)
