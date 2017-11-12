from acelib cimport math3d_c

cdef class Vector3:
    cdef:
        math3d_c.Vector3[double] *c_vec
        bint is_ref
    cpdef void set(self, double x, double y, double z)
    cpdef void normalize(self)
    cpdef double sq_magnitude(self)
    cpdef double magnitude(self)
    cpdef double sq_distance(self, Vector3 other)
    cpdef double distance(self, Vector3 other)
    cpdef double dot(self, Vector3 other)
    cpdef double angle(self, Vector3 other, bint deg=*)
    cpdef bint equals(self, Vector3 other, double tolerance=*)
    cpdef Vector3 cross(self, Vector3 other)
    cpdef Vector3 lerp(self, Vector3 other, double t, bint clamped=*)
    cpdef Vector3 scale(self, Vector3 other)
    cpdef Vector3 max(self, Vector3 other)
    cpdef Vector3 min(self, Vector3 other)


cdef inline Vector3 new_vector3_from(math3d_c.Vector3[double] &other):
    cdef Vector3 vec = Vector3()
    vec.c_vec.x = other.x
    vec.c_vec.y = other.y
    vec.c_vec.z = other.z
    return vec


cdef inline Vector3 new_vector3(double x, double y, double z):
    cdef Vector3 vec = Vector3()
    vec.c_vec.x = x
    vec.c_vec.y = y
    vec.c_vec.z = z
    return vec


cdef inline Vector3 new_proxy_vector(math3d_c.Vector3[double] *other):
    cdef Vector3 vec = Vector3(ref=True)
    vec.c_vec = other
    return vec
