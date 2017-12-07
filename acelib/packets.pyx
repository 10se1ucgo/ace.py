cimport cython
from libc.stdint cimport *
from libc.math cimport NAN, isnan
from libcpp cimport bool

from acelib.bytes cimport ByteReader, ByteWriter
from acelib.util cimport read_position, write_position, read_color, write_color
from acelib import constants


@cython.freelist(64)
cdef class Color:
    cdef public:
        uint8_t r, g, b

    def __cinit__(self, uint8_t r=0, uint8_t g=0, uint8_t b=0):
        self.r = r; self.g = g; self.b = b

    cpdef read(self, ByteReader reader):
        read_color(reader, &self.r, &self.g, &self.b)

    cpdef write(self, ByteWriter writer):
        write_color(writer, self.r, self.g, self.b)

    cpdef set(self, uint8_t r, uint8_t g, uint8_t b):
        self.r = r; self.g = g; self.b = b

    @property
    def rgb(self):
        return self.r, self.g, self.b

    @rgb.setter
    def rgb(self, value):
        self.r, self.g, self.b = value


@cython.freelist(64)
cdef class Pos3f:
    cdef public:
        float x, y, z

    def __cinit__(self, float x=0, float y=0, float z=0):
        self.x = x; self.y = y; self.z = z

    cpdef read(self, ByteReader reader):
        read_position(reader, &self.x, &self.y, &self.z)

    cpdef write(self, ByteWriter writer):
        write_position(writer, self.x, self.y, self.z)

    cpdef set(self, uint8_t x, uint8_t y, uint8_t z):
        self.x = x; self.y = y; self.z = z

    @property
    def xyz(self):
        return self.x, self.y, self.z

    @xyz.setter
    def xyz(self, value):
        self.x, self.y, self.z = value


@cython.freelist(512)
cdef class Loader:
    id: int = -1

    def __init__(self, ByteReader reader = None):
        if reader:
            self.read(reader)

    cpdef read(self, ByteReader reader):
        raise NotImplementedError

    cpdef write(self, ByteWriter reader):
        raise NotImplementedError

    cpdef ByteWriter generate(self):
        cdef ByteWriter writer = ByteWriter()
        self.write(writer)
        return writer


cdef class InitialInfo(Loader):
    id: int = 0

    cdef public:
        str mode_name, mode_description

    cpdef read(self, ByteReader reader):
        # apparently these are unicode, which means everything else probably is too.
        self.mode_name = reader.read_bytes().decode("utf8")
        self.mode_description = reader.read_bytes().decode("utf8")

    cpdef write(self, ByteWriter writer):
        writer.write_uint8(self.id)
        writer.write_bytes(self.mode_name.encode("utf8"))
        writer.write_bytes(self.mode_description.encode("utf8"))

cdef class PositionData(Loader):
    id: int = 1

    cdef public:
        Pos3f data

    def __cinit__(self):
        self.data = Pos3f()

    cpdef read(self, ByteReader reader):
        self.data.read(reader)

    cpdef write(self, ByteWriter writer):
        writer.write_uint8(self.id)
        self.data.write(writer)


cdef class ClientUpdateData:
    cdef public:
        Pos3f p, o

    def __cinit__(self, px=0, py=0, pz=0, ox=0, oy=0, oz=0):
        self.p = Pos3f(px, py, pz)
        self.o = Pos3f(ox, oy, oz)

    cpdef read(self, ByteReader reader):
        self.p.read(reader)
        self.o.read(reader)

    cpdef write(self, ByteWriter writer):
        self.p.write(writer)
        self.o.write(writer)


cdef class PositionOrientationData(Loader):
    id: int = 2

    cdef public:
        ClientUpdateData data

    def __cinit__(self):
        self.data = ClientUpdateData()

    cpdef read(self, ByteReader reader):
        self.data.read(reader)

    cpdef write(self, ByteWriter writer):
        writer.write_uint8(self.id)
        self.data.write(writer)


cdef class WorldUpdate(Loader):
    id: int = 3

    cdef:
        dict data

    cpdef read(self, ByteReader reader):
        self.data = {}

        cdef uint8_t p_id

        while reader.data_left():
            p_id = reader.read_uint8()
            self.data[p_id] = ClientUpdateData().read(reader)

    cpdef write(self, ByteWriter writer):
        writer.write_uint8(self.id)

        cdef:
            uint8_t player_id
            ClientUpdateData cud

        for player_id, cud in self.data.items():
            writer.write_uint8(player_id)
            cud.write(writer)

    def clear(self):
        self.data = {}

    def __setitem__(self, uint8_t key, value):
        self.data[key] = ClientUpdateData(*value[0], *value[1])


cdef class InputData(Loader):
    id: int = 4

    cdef public:
        uint8_t player_id
        bint up, down, left, right, jump, crouch, sneak, sprint

    cpdef read(self, ByteReader reader):
        self.player_id = reader.read_uint8()

        cdef uint8_t flags = reader.read_uint8()
        self.up     = flags & (1 << 0)
        self.down   = flags & (1 << 1)
        self.left   = flags & (1 << 2)
        self.right  = flags & (1 << 3)
        self.jump   = flags & (1 << 4)
        self.crouch = flags & (1 << 5)
        self.sneak  = flags & (1 << 6)
        self.sprint = flags & (1 << 7)

    cpdef write(self, ByteWriter writer):
        writer.write_uint8(self.id)
        writer.write_uint8(self.player_id)

        cdef uint8_t flags = (
            <bool>self.up     << 0 |
            <bool>self.down   << 1 |
            <bool>self.left   << 2 |
            <bool>self.right  << 3 |
            <bool>self.jump   << 4 |
            <bool>self.crouch << 5 |
            <bool>self.sneak  << 6 |
            <bool>self.sprint << 7
        )
        writer.write_uint8(flags)


cdef class WeaponInput(Loader):
    id: int = 5

    cdef public:
        uint8_t player_id
        bint primary, secondary

    cpdef read(self, ByteReader reader):
        self.player_id = reader.read_uint8()

        cdef uint8_t flags = reader.read_uint8()
        self.primary   = flags & (1 << 0)
        self.secondary = flags & (1 << 1)

    cpdef write(self, ByteWriter reader):
        reader.write_uint8(self.id)
        reader.write_uint8(self.player_id)

        cdef uint8_t flags = <bool>self.primary << 0 | <bool>self.secondary << 1
        reader.write_uint8(flags)


cdef class HitPacket(Loader):
    id: int = 6

    cdef public:
        uint8_t player_id, value

    cpdef read(self, ByteReader reader):
        self.player_id = reader.read_uint8()
        self.value = reader.read_uint8()

    cpdef write(self, ByteWriter writer):
        writer.write_uint8(self.id)
        writer.write_uint8(self.player_id)
        writer.write_uint8(self.value)


cdef class SetHP(Loader):
    id: int = 6

    cdef public:
        uint8_t hp, type
        Pos3f source

    def __cinit__(self):
        self.source = Pos3f()

    cpdef read(self, ByteReader reader):
        self.hp = reader.read_uint8()
        self.type = reader.read_uint8()
        self.source.read(reader)

    cpdef write(self, ByteWriter writer):
        writer.write_uint8(self.id)
        writer.write_uint8(self.hp)
        writer.write_uint8(self.type)
        self.source.write(writer)


cdef class UseOrientedItem(Loader):
    id: int = 7

    cdef public:
        uint8_t player_id, tool
        float value
        Pos3f position, velocity

    def __cinit__(self):
        self.position = Pos3f()
        self.velocity = Pos3f()

    cpdef read(self, ByteReader reader):
        self.player_id = reader.read_uint8()
        self.tool = reader.read_uint8()
        self.value = reader.read_float()
        self.position.read(reader)
        self.velocity.read(reader)

    cpdef write(self, ByteWriter writer):
        writer.write_uint8(self.id)
        writer.write_uint8(self.player_id)
        writer.write_uint8(self.tool)
        writer.write_float(self.value)
        self.position.write(writer)
        self.velocity.write(writer)


cdef class SetTool(Loader):
    id: int = 8

    cdef public:
        uint8_t player_id, value

    cpdef read(self, ByteReader reader):
        self.player_id = reader.read_uint8()
        self.value = reader.read_uint8()

    cpdef write(self, ByteWriter writer):
        writer.write_uint8(self.id)
        writer.write_uint8(self.player_id)
        writer.write_uint8(self.value)


cdef class SetColor(Loader):
    id: int = 9

    cdef public:
        uint8_t player_id
        Color color

    def __cinit__(self):
        self.color = Color()

    cpdef read(self, ByteReader reader):
        self.player_id = reader.read_uint8()
        self.color.read(reader)

    cpdef write(self, ByteWriter writer):
        writer.write_uint8(self.id)
        writer.write_uint8(self.player_id)
        self.color.write(writer)


cdef class ExistingPlayer(Loader):
    id: int = 10

    cdef public:
        uint8_t player_id, weapon, tool
        int8_t team
        uint32_t kills
        Color color
        str name

    def __cinit__(self):
        self.color = Color()

    cpdef read(self, ByteReader reader):
        self.player_id = reader.read_uint8()
        self.team = reader.read_int8()
        self.weapon = reader.read_uint8()
        self.tool = reader.read_uint8()
        self.kills = reader.read_uint32()
        self.color.read(reader)
        self.name = reader.read_bytes().decode("utf8")

    cpdef write(self, ByteWriter writer):
        writer.write_uint8(self.id)
        writer.write_uint8(self.player_id)
        writer.write_int8(self.team)
        writer.write_uint8(self.weapon)
        writer.write_uint8(self.tool)
        writer.write_uint32(self.kills)
        self.color.write(writer)
        writer.write_bytes(self.name.encode("utf8"))


cdef class ShortPlayerData(Loader):
    id: int = 11

    cdef public:
        uint8_t player_id, weapon
        int8_t team

    cpdef read(self, ByteReader reader):
        self.player_id = reader.read_uint8()
        self.team = reader.read_int8()
        self.weapon = reader.read_uint8()

    cpdef write(self, ByteWriter writer):
        writer.write_uint8(self.id)
        writer.write_uint8(self.player_id)
        writer.write_int8(self.team)
        writer.write_uint8(self.weapon)


cdef class Entity(Loader):
    cdef public:
        uint8_t id, type, state
        int8_t carrier
        Pos3f position
        float yaw

    def __cinit__(self):
        self.position = Pos3f()

    cpdef read(self, ByteReader reader):
        self.id = reader.read_uint8()
        self.type = reader.read_uint8()
        self.state = reader.read_uint8()
        self.carrier = reader.read_int8()
        self.position.read(reader)
        self.yaw = reader.read_float()

    cpdef write(self, ByteWriter writer):
        writer.write_uint8(self.id)
        writer.write_uint8(self.type)
        writer.write_uint8(self.state)
        writer.write_int8(self.carrier)
        self.position.write(writer)
        writer.write_float(self.yaw)


cdef class ChangeEntity(Loader):
    id: int = 12

    cdef public:
        # yes, this is basically Entity, except `type` is the action to perform on the entity, not the Entity type.
        # Also, certain fields are only written based on the change type.
        # Also you can't set the yaw(?).
        uint8_t entity_id, type, state
        int8_t carrier
        Pos3f position

    def __cinit__(self):
        self.position = Pos3f()

    cpdef read(self, ByteReader reader):
        self.entity_id = reader.read_uint8()
        self.type = reader.read_uint8()
        if self.type == constants.SET.POSITION.value:
            self.position.read(reader)
        elif self.type == constants.SET.CARRIER.value:
            self.carrier = reader.read_int8()
        elif self.type == constants.SET.STATE.value:
            self.state = reader.read_uint8()

    cpdef write(self, ByteWriter writer):
        writer.write_uint8(self.id)
        writer.write_uint8(self.entity_id)
        writer.write_uint8(self.type)
        if self.type == constants.SET.POSITION.value:
            self.position.write(writer)
        elif self.type == constants.SET.CARRIER.value:
            writer.write_int8(self.carrier)
        elif self.type == constants.SET.STATE.value:
            writer.write_uint8(self.state)


cdef class DestroyEntity(Loader):
    id: int = 13

    cdef public:
        uint8_t entity_id

    cpdef read(self, ByteReader reader):
        self.entity_id = reader.read_uint8()

    cpdef write(self, ByteWriter writer):
        writer.write_uint8(self.id)
        writer.write_uint8(self.entity_id)

    def set_entity(self, entity):
        self.entity_id = entity.id


cdef class CreateEntity(Loader):
    id: int = 14

    cdef public:
        Entity entity

    cpdef read(self, ByteReader reader):
        self.entity = Entity()
        self.entity.read(reader)

    cpdef write(self, ByteWriter writer):
        writer.write_uint8(self.id)
        self.entity.write(writer)

    def set_entity(self, entity):
        self.entity = entity
        # This is done likely because a newly created entity doesn't have a carrier
        self.entity.carrier = -1
        # Not sure why this is done. Setting entity directly with CreateEntity().entity doesn't do this.
        self.entity.state = constants.TEAM.NEUTRAL.value


cdef class PlaySound(Loader):
    id: int = 15

    cdef public:
        str name
        bint looping, positioned
        uint8_t loop_id
        Pos3f position

    def __cinit__(self):
        self.position = Pos3f()

    cpdef read(self, ByteReader reader):
        self.name = reader.read_bytes().decode("utf8")

        cdef uint8_t flags = reader.read_uint8()
        self.looping    = flags & (1 << 0)
        self.positioned = flags & (1 << 1)

        if self.looping:
            self.loop_id = reader.read_uint8()
        if self.positioned:
            self.position.read(reader)

    cpdef write(self, ByteWriter writer):
        writer.write_uint8(self.id)
        writer.write_bytes(self.name.encode("utf8"))

        cdef int sound_flags = <bool>self.looping << 0 | <bool>self.positioned << 1
        writer.write_uint8(sound_flags)

        if self.looping:
            writer.write_uint8(self.loop_id)
        if self.positioned:
            self.position.write(writer)


cdef class StopSound(Loader):
    id: int = 16

    cdef public:
        uint8_t loop_id

    cpdef read(self, ByteReader reader):
        self.loop_id = reader.read_uint8()

    cpdef write(self, ByteWriter writer):
        writer.write_uint8(self.id)
        writer.write_uint8(self.loop_id)


cdef class CreatePlayer(Loader):
    id: int = 17

    cdef public:
        uint8_t player_id, weapon
        int8_t team
        Pos3f position
        str name

    def __cinit__(self):
        self.position = Pos3f()

    cpdef read(self, ByteReader reader):
        self.player_id = reader.read_uint8()
        self.weapon = reader.read_uint8()
        self.team = reader.read_int8()
        self.position.read(reader)
        self.name = reader.read_bytes().decode("utf8")

    cpdef write(self, ByteWriter writer):
        writer.write_uint8(self.id)
        writer.write_uint8(self.player_id)
        writer.write_uint8(self.weapon)
        writer.write_int8(self.team)
        self.position.write(writer)
        writer.write_bytes(self.name.encode("utf8"))


cdef class BlockAction(Loader):
    id: int = 18

    cdef public:
        uint8_t player_id, value
        int32_t x, y, z

    cpdef read(self, ByteReader reader):
        self.player_id = reader.read_uint8()
        self.value = reader.read_uint8()
        self.x = reader.read_int32()
        self.y = reader.read_int32()
        self.z = reader.read_int32()

    cpdef write(self, ByteWriter writer):
        writer.write_uint8(self.id)
        writer.write_uint8(self.player_id)
        writer.write_uint8(self.value)
        writer.write_int32(self.x)
        writer.write_int32(self.y)
        writer.write_int32(self.z)

    @property
    def xyz(self):
        return self.x, self.y, self.z

    @xyz.setter
    def xyz(self, value):
        self.x, self.y, self.z = value


cdef class ServerBlockItem(Loader):
    cdef public:
        uint8_t x, y, z
        Color color

    cpdef read(self, ByteReader reader):
        cdef bint has_color = reader.read_uint8()
        self.x = reader.read_uint8()
        self.y = reader.read_uint8()
        self.z = reader.read_uint8()
        if has_color:
            self.color = Color().read(reader)
        else:
            self.color = None

    cpdef write(self, ByteWriter writer):
        cdef bint has_color = self.color is not None
        writer.write_uint8(has_color)
        writer.write_uint8(self.x)
        writer.write_uint8(self.y)
        writer.write_uint8(self.z)
        if has_color:
            self.color.write(writer)

    @property
    def xyz(self):
        return self.x, self.y, self.z

    @xyz.setter
    def xyz(self, value):
        self.x, self.y, self.z = value


cdef class ServerBlockAction(Loader):
    id: int = 19

    cdef public:
        list items

    cpdef read(self, ByteReader reader):
        cdef uint32_t size  = reader.read_uint32()
        for x in range(size):
            block = ServerBlockItem()
            block.read(reader)
            self.items.append(block)

    cpdef write(self, ByteWriter writer):
        writer.write_uint8(self.id)
        writer.write_uint32(len(self.items))

        cdef ServerBlockItem block
        for block in self.items:
            block.write(writer)

    def add_block(self, uint8_t x, uint8_t y, uint8_t z, Color color):
        block = ServerBlockItem()
        block.x = x
        block.y = y
        block.z = z
        block.color = color
        self.items.append(block)

    def remove_block(self, x, y, z):
        # this could probably be more efficient :P
        self.items = [block for block in self.items if (block.x, block.y, block.z) != (x, y, z)]

    def reset(self):
        self.items = []


cdef class BlockLine(Loader):
    id: int = 20

    cdef public:
        uint8_t player_id
        int32_t x1, y1, z1, x2, y2, z2

    cpdef read(self, ByteReader reader):
        self.player_id = reader.read_uint8()
        self.x1 = reader.read_int32()
        self.y1 = reader.read_int32()
        self.z1 = reader.read_int32()
        self.x2 = reader.read_int32()
        self.y2 = reader.read_int32()
        self.z2 = reader.read_int32()

    cpdef write(self, ByteWriter writer):
        writer.write_uint8(self.id)
        writer.write_uint8(self.player_id)
        writer.write_int32(self.x1)
        writer.write_int32(self.y1)
        writer.write_int32(self.z1)
        writer.write_int32(self.x2)
        writer.write_int32(self.y2)
        writer.write_int32(self.z2)

    @property
    def xyz1(self):
        return self.x1, self.y1, self.z1

    @xyz1.setter
    def xyz1(self, value):
        self.x1, self.y1, self.z1 = value

    @property
    def xyz2(self):
        return self.x2, self.y2, self.z2

    @xyz2.setter
    def xyz2(self, value):
        self.x2, self.y2, self.z2 = value


cdef class StateData(Loader):
    id: int = 21

    cdef public:
        uint8_t player_id
        Color fog_color, team1_color, team2_color
        uint8_t team1_score, team2_score, score_limit
        str team1_name, team2_name, mode_name
        list entities

    def __cinit__(self):
        self.fog_color = Color()
        self.team1_color = Color()
        self.team2_color = Color()
        self.entities = []

    cpdef read(self, ByteReader reader):
        self.player_id = reader.read_uint8()
        self.fog_color.read(reader)
        self.team1_color.read(reader)
        self.team2_color.read(reader)
        self.team1_score = reader.read_uint8()
        self.team2_score = reader.read_uint8()
        self.score_limit = reader.read_uint8()
        self.team1_name = reader.read_bytes().decode("utf8")
        self.team2_name = reader.read_bytes().decode("utf8")
        self.mode_name = reader.read_bytes().decode("utf8")
        while reader.data_left():
            self.entities.append(Entity(reader))

    cpdef write(self, ByteWriter writer):
        writer.write_uint8(self.id)
        writer.write_uint8(self.player_id)
        self.fog_color.write(writer)
        self.team1_color.write(writer)
        self.team2_color.write(writer)
        writer.write_uint8(self.team1_score)
        writer.write_uint8(self.team2_score)
        writer.write_uint8(self.score_limit)
        writer.write_bytes(self.team1_name.encode("utf8"))
        writer.write_bytes(self.team2_name.encode("utf8"))
        writer.write_bytes(self.mode_name.encode("utf8"))
        for ent in self.entities:
            ent.write(writer)

    def set_entities(self, entities):
        for ent in entities:
            ent.state = constants.TEAM.NEUTRAL.value
            ent.carrier = -1
            self.entities.append(ent)


cdef class KillAction(Loader):
    id: int = 22

    cdef public:
        uint8_t player_id, killer_id, kill_type, respawn_time

    cpdef read(self, ByteReader reader):
        self.player_id = reader.read_uint8()
        self.killer_id = reader.read_uint8()
        self.kill_type = reader.read_uint8()
        self.respawn_time = reader.read_uint8()

    cpdef write(self, ByteWriter writer):
        writer.write_uint8(self.id)
        writer.write_uint8(self.player_id)
        writer.write_uint8(self.killer_id)
        writer.write_uint8(self.kill_type)
        writer.write_uint8(self.respawn_time)


cdef class ChatMessage(Loader):
    id: int = 23

    cdef public:
        uint8_t player_id, chat_type
        str value

    cpdef read(self, ByteReader reader):
        self.player_id = reader.read_uint8()
        self.chat_type = reader.read_uint8()
        self.value = reader.read_bytes().decode("utf8")

    cpdef write(self, ByteWriter writer):
        writer.write_uint8(self.id)
        writer.write_uint8(self.player_id)
        writer.write_uint8(self.chat_type)
        writer.write_bytes(self.value.encode("utf8"))


cdef class MapStart(Loader):
    id: int = 24

    cdef public:
        uint32_t size

    cpdef read(self, ByteReader reader):
        self.size = reader.read_uint32()

    cpdef write(self, ByteWriter writer):
        writer.write_uint8(self.id)
        writer.write_uint32(self.size)


cdef class MapChunk(Loader):
    id: int = 25

    cdef public:
        bytes data

    cpdef read(self, ByteReader reader):
        self.data = reader.get()

    cpdef write(self, ByteWriter writer):
        writer.write_uint8(self.id)
        writer.write(self.data)


cdef class PackStart(Loader):
    id: int = 26

    cdef public:
        uint32_t size, checksum

    cpdef read(self, ByteReader reader):
        self.size = reader.read_uint32()
        self.checksum = reader.read_uint32()

    cpdef write(self, ByteWriter writer):
        writer.write_uint8(self.id)
        writer.write_uint32(self.size)
        writer.write_uint32(self.checksum)


cdef class PackResponse(Loader):
    id: int = 27

    cdef public:
        bint value

    cpdef read(self, ByteReader reader):
        self.value = reader.read_uint8()

    cpdef write(self, ByteWriter writer):
        writer.write_uint8(self.id)
        writer.write_uint8(self.value)


cdef class PackChunk(Loader):
    id: int = 28

    cdef public:
        bytes data

    cpdef read(self, ByteReader reader):
        self.data = reader.get()

    cpdef write(self, ByteWriter writer):
        writer.write_uint8(self.id)
        writer.write(self.data)


cdef class PlayerLeft(Loader):
    id: int = 29

    cdef public:
        uint8_t player_id

    cpdef read(self, ByteReader reader):
        self.player_id = reader.read_uint8()

    cpdef write(self, ByteWriter writer):
        writer.write_uint8(self.id)
        writer.write_uint8(self.player_id)


cdef class ProgressBar(Loader):
    id: int = 30

    cdef public:
        float progress, rate
        Color color1, color2

    def __cinit__(self):
        self.color1 = Color()
        self.color2 = Color()

    cpdef read(self, ByteReader reader):
        self.progress = reader.read_float()
        if isnan(self.progress):
            return
        self.rate = reader.read_float()
        self.color1.read(reader)
        self.color2.read(reader)

    cpdef write(self, ByteWriter writer):
        writer.write_uint8(self.id)
        writer.write_float(self.progress)
        if isnan(self.progress):
            return
        writer.write_float(self.rate)
        self.color1.write(writer)
        self.color2.write(writer)

    def set(self, float progress, float rate):
        self.progress = progress
        self.rate = rate

    @property
    def stopped(self):
        return isnan(self.progress)

    @stopped.setter
    def stopped(self, value):
        if value:
            self.progress = NAN
        else:
            self.progress = 0.0


cdef class Restock(Loader):
    id: int = 31

    cdef public:
        uint8_t player_id

    cpdef read(self, ByteReader reader):
        self.player_id = reader.read_uint8()

    cpdef write(self, ByteWriter writer):
        writer.write_uint8(self.id)
        writer.write_uint8(self.player_id)


cdef class FogColor(Loader):
    id: int = 32

    cdef public:
        Color color

    def __cinit__(self):
        self.color = Color()

    cpdef read(self, ByteReader reader):
        reader.read_uint8()
        self.color.read(reader)

    cpdef write(self, ByteWriter writer):
        writer.write_uint8(self.id)
        writer.write_uint8(0xFF)
        self.color.write(writer)


cdef class WeaponReload(Loader):
    id: int = 33

    cdef public:
        uint8_t player_id, clip_ammo, reserve_ammo

    cpdef read(self, ByteReader reader):
        self.player_id = reader.read_uint8()
        self.clip_ammo = reader.read_uint8()
        self.reserve_ammo = reader.read_uint8()

    cpdef write(self, ByteWriter writer):
        writer.write_uint8(self.id)
        writer.write_uint8(self.player_id)
        writer.write_uint8(self.clip_ammo)
        writer.write_uint8(self.reserve_ammo)


cdef class ChangeTeam(Loader):
    id: int = 34

    cdef public:
        uint8_t player_id
        int8_t team

    cpdef read(self, ByteReader reader):
        self.player_id = reader.read_uint8()
        self.team = reader.read_int8()

    cpdef write(self, ByteWriter writer):
        writer.write_uint8(self.id)
        writer.write_uint8(self.player_id)
        writer.write_int8(self.team)


cdef class ChangeClass(Loader):
    id: int = 35

    cdef public:
        uint8_t player_id, class_id

    cpdef read(self, ByteReader reader):
        self.player_id = reader.read_uint8()
        self.class_id = reader.read_uint8()

    cpdef write(self, ByteWriter reader):
        reader.write_uint8(self.id)
        reader.write_uint8(self.player_id)
        reader.write_uint8(self.class_id)


cdef class SetScore(Loader):
    id: int = 36

    cdef public:
        uint8_t type, specifier
        uint16_t value

    cpdef read(self, ByteReader reader):
        self.type = reader.read_uint8()
        self.specifier = reader.read_uint8()
        self.value = reader.read_uint16()

    cpdef write(self, ByteWriter reader):
        reader.write_uint8(self.id)
        reader.write_uint8(self.type)
        reader.write_uint8(self.specifier)
        reader.write_uint16(self.value)


cdef class UseCommand(Loader):
    id: int = 37

    cpdef read(self, ByteReader reader):
        pass

    cpdef write(self, ByteWriter reader):
        reader.write_uint8(self.id)


cdef class PlaceMG(Loader):
    id: int = 38

    cdef public:
        Pos3f pos
        float yaw

    def __cinit__(self):
        self.pos = Pos3f()

    cpdef read(self, ByteReader reader):
        self.pos.read(reader)
        self.yaw = reader.read_float()

    cpdef write(self, ByteWriter writer):
        writer.write_uint8(self.id)
        self.pos.write(writer)
        writer.write_float(self.yaw)



LOADERS = Loader.__subclasses__()

cdef set SERVER_ONLY_LOADERS = {SetHP}
cdef set CLIENT_ONLY_LOADERS = {HitPacket}

SERVER_LOADERS = {loader.id: loader for loader in LOADERS if loader not in CLIENT_ONLY_LOADERS}
CLIENT_LOADERS = {loader.id: loader for loader in LOADERS if loader not in SERVER_ONLY_LOADERS}
