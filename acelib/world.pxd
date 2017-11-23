# from .vxl cimport VXLMap, AceMap
from acelib cimport math3d_c, math3d, vxl
from libcpp cimport bool

cdef extern from "world_c.cpp" nogil:
    cdef cppclass AcePlayer:
        AcePlayer(vxl.AceMap *map) except +
        long update(double dt, double time)
        void set_orientation(double x, double y, double z)

        vxl.AceMap *map
        bool mf, mb, ml, mr, jump, crouch, sneak, sprint, primary_fire, secondary_fire, airborne, wade, alive, weapon
        float lastclimb
        math3d_c.Vector3[double] p, e, v, f, s, h

    cdef cppclass AceGrenade:
        AceGrenade(vxl.AceMap *map, math3d_c.Vector3[double] position, math3d_c.Vector3[double] velocity) except +
        AceGrenade(vxl.AceMap *map, double px, double py, double pz, double vx, double vy, double vz) except +
        bool update(double dt, double time)
        bool next_collision(double dt, double max, double *eta, math3d_c.Vector3[double] *pos)

        vxl.AceMap *map
        math3d_c.Vector3[double] p, v

    bool c_cast_ray "cast_ray" (vxl.AceMap *map,
                                const math3d_c.Vector3[double] &position, const math3d_c.Vector3[double] &direction,
                                long *x, long *y, long *z, float length, bool isdirection)

    bool clipbox(vxl.AceMap *map, float x, float y, float z)

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
        math3d.Vector3 position, velocity, orientation, eye


cdef class Grenade:
    cdef AceGrenade *grenade
    cdef public:
        math3d.Vector3 position, velocity


cdef class GenericMovement:
    cdef public:
        vxl.VXLMap map
        math3d.Vector3 position
