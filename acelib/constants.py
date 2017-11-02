from enum import IntEnum

class WeaponType(IntEnum):
    SEMI = 0
    SMG = 1
    SHOTGUN = 2
    RPG = 3


class HitType(IntEnum):
    TORSO = 0
    HEAD = 1
    ARMS = 2
    LEGS = 3
    MELEE = 4


class ToolType(IntEnum):
    SPADE = 0
    BLOCK = 1
    WEAPON = 2
    GRENADE = 3
    RPG = 4


class BAType(IntEnum):
    BUILD = 0
    DESTROY = 1
    SPADE = 2
    GRENADE = 3


class ChatType(IntEnum):
    ALL = 0
    TEAM = 1
    SYSTEM = 2
    BIG = 3


class ScoreType(IntEnum):
    TEAM = 0
    PLAYER = 1


class EntityType(IntEnum):
    FLAG = 0
    BASE = 1
    HELICOPTER = 2
    AMMO_CRATE = 3
    HEALTH_CRATE = 4


class KillType(IntEnum):
    WEAPON = 0
    HEADSHOT = 1
    MELEE = 2
    GRENADE = 3
    FALL = 4
    TEAM_CHANGE = 5
    CLASS_CHANGE = 6


class DisconnectType(IntEnum):
    UNDEFINED = 0
    BANNED = 1
    KICKED = 2
    WRONG_VERSION = 3
    FULL = 4


class ChangeEntityType(IntEnum):
    SET_STATE = 0
    SET_POSITION = 1
    SET_CARRIER = 2


class DamageType(IntEnum):
    SELF = 0
    OTHER = 1
    HEAL = 3


class TeamType(IntEnum):
    SPECTATOR = -1
    TEAM1 = 0
    TEAM2 = 1
    NEUTRAL = 2


TC_CAPTURE_DISTANCE = 16
TC_CAPTURE_RATE = 0.05

MIN_TERRITORY_COUNT = 3
MAX_TERRITORY_COUNT = 7

SPAWN_RADIUS = 32

MELEE_DISTANCE = 3

MAX_CHAT_SIZE = 90

UPDATE_FPS = 60.0
UPDATE_FREQUENCY = 1 / UPDATE_FPS
NETWORK_FPS = 10.0

MAX_DAMAGE = 2

ROCKET_SPEED = 45.0
ROCKET_FALLOFF = 25.0

PROTOCOL_VERSION = 3
