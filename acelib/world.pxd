from .vxl cimport VXLMap, AceMap
from . cimport math3d_c, math3d
from libcpp cimport bool

cdef extern from "world_c.cpp" nogil:
    cdef cppclass AcePlayer:
        AcePlayer(AceMap *map) except +

        AceMap *map
        bool mf, mb, ml, mr, jump, crouch, sneak, sprint, primary_fire, secondary_fire
        float lastclimb
        int airborne, wade, alive, weapon
        math3d_c.Vector3[double] p, e, v, f, s, h

    long move_player(AcePlayer *p, double dt, double time)
    void reorient_player(AcePlayer *p, float x, float y, float z)


# cdef class World:
#     cdef public:
#         VXLMap map
#         list objects
#
#     # cpdef delete_object(self, WorldObject item)


cdef class WorldObject:
    cdef public:
        str name
        VXLMap map

    cdef long update(self, double dt, double time)


cdef class Player:
    cdef AcePlayer *ply
    cdef public:
        math3d.Vector3 position, velocity, orientation

