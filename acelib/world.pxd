# from .vxl cimport VXLMap, AceMap
from acelib cimport math3d_c, math3d, vxl
from libcpp cimport bool

cdef extern from "world_c.cpp" nogil:
    cdef cppclass AcePlayer:
        AcePlayer(vxl.AceMap *map) except +

        vxl.AceMap *map
        bool mf, mb, ml, mr, jump, crouch, sneak, sprint, primary_fire, secondary_fire, airborne, wade, alive, weapon
        float lastclimb
        math3d_c.Vector3[double] p, e, v, f, s, h

        long update(double dt, double time)
        void set_orientation(double x, double y, double z)


# cdef class World:
#     cdef public:
#         VXLMap map
#         list objects
#
#     # cpdef delete_object(self, WorldObject item)


cdef class WorldObject:
    cdef public:
        str name
        vxl.VXLMap map

    cdef long update(self, double dt, double time)


cdef class Player:
    cdef AcePlayer *ply
    cdef public:
        math3d.Vector3 position, velocity, orientation

