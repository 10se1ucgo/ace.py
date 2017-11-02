from acelib import packets, math3d
from acelib.constants import *

from . import protocol, team, connection, util
from .loaders import *

class Entity:
    type = None
    mountable = False

    def __init__(self, id: int, protocol: 'protocol.ServerProtocol', **kwargs):
        self.id = id
        self.protocol = protocol

        self.position: math3d.Vector3 = math3d.Vector3(*kwargs.get("position"))
        self.team: team.Team = kwargs.get("team")
        self.carrier: connection.ServerConnection = kwargs.get("carrier")

        # self.old_team = self.team
        # self.old_pos = self.position.xyz
        # self.old_ply = self.carrier

        self.destroyed = False

        self.on_collide = util.Event()

    # def set(self, *args, **kwargs):
    #     Vertex3.set(self, *args, **kwargs)
    #     change_entity.type = SET_POSITION
    #     change_entity.x, change_entity.y, change_entity.z = self.get()
    #     self.protocol.send_contained(change_entity, save=True)
    #     self.old_pos = self.get()

    async def update(self, dt):
        if self.destroyed:
            return

        z = self.protocol.map.get_z(self.position.x, self.position.y)
        if z != self.position.z:
            await self.set_position(self.position.x, self.position.y, z)

        if not self.carrier:
            for conn in self.protocol.players.values():
                dist = self.position.sq_distance(conn.position)
                if dist <= 3 ** 2:
                    self.on_collide(self, conn)
        #
        # await self.change()

    async def set_team(self, team):
        if self.destroyed:
            return
        self.team = team
        state = self.team.id if self.team else TeamType.NEUTRAL
        change_entity.type = ChangeEntityType.SET_STATE
        change_entity.state = state
        self.protocol.broadcast_loader(change_entity)

    async def set_position(self, x, y, z):
        if self.destroyed:
            return
        self.position.xyz = x, y, z
        change_entity.type = ChangeEntityType.SET_POSITION
        change_entity.position.xyz = self.position.xyz
        await self.protocol.broadcast_loader(change_entity)
        self.old_pos = self.position.xyz

    async def set_carrier(self, carrier=None):
        if self.destroyed:
            return
        self.carrier = carrier
        player = self.carrier.id if self.carrier else -1
        change_entity.type = ChangeEntityType.SET_CARRIER
        change_entity.carrier = player
        await self.protocol.broadcast_loader(change_entity)
        self.old_ply = self.carrier

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
        ent.state = TeamType.NEUTRAL if self.team is None else self.team.id
        return ent

    # async def change(self, force=False):
    #     if self.destroyed:
    #         return
    #     change_entity.entity_id = self.id
    #
    #     if force or self.team != self.old_team:
    #         state = self.team.id if self.team else TeamType.NEUTRAL
    #         change_entity.type = ChangeEntityType.SET_STATE
    #         change_entity.state = state
    #         self.protocol.broadcast_loader(change_entity)
    #         self.old_team = self.team
    #
    #     if force or self.old_pos != self.position.xyz:
    #         change_entity.type = ChangeEntityType.SET_POSITION
    #         change_entity.position.xyz = self.position.xyz
    #         await self.protocol.broadcast_loader(change_entity)
    #         self.old_pos = self.position.xyz
    #
    #     if force or self.carrier != self.old_ply:
    #         player = self.carrier.id if self.carrier else -1
    #         change_entity.type = ChangeEntityType.SET_CARRIER
    #         change_entity.carrier = player
    #         await self.protocol.broadcast_loader(change_entity)
    #         self.old_ply = self.carrier

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return f"<Entity(id={self.id}, type={self.type!r}, pos={self.position})>"


class Flag(Entity):
    type = EntityType.FLAG


class AmmoCrate(Entity):
    type = EntityType.AMMO_CRATE


class HealthCrate(Entity):
    type = EntityType.HEALTH_CRATE


class Base(Entity):
    type = EntityType.BASE


# def collide():
#     return (math.fabs(vec1.x - vec2.x) < distance and
#             math.fabs(vec1.y - vec2.y) < distance and
#             math.fabs(vec1.z - vec2.z) < distance)
