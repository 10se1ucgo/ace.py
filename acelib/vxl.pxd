# distutils: sources = acelib/vxl_c.cpp
from libc.stdint cimport *
from libcpp.vector cimport vector
from libcpp cimport bool

cdef extern from "vxl_c.h" nogil:
    struct Pos3:
        int x, y, z

    cdef cppclass AceMap:
        AceMap(uint8_t *buf) except +
        void read(uint8_t *buf) except +
        vector[uint8_t] write() except +
        size_t write(vector[uint8_t] &v, int *sx, int *sy, int columns);

        bool is_surface(int x, int y, int z) except +
        bool get_solid(int x, int y, int z, bool wrapped=False) except +
        uint32_t get_color(int x, int y, int z, bool wrapped=False) except +
        int get_z(int x, int y, int start) except +
        void get_random_point(int *x, int *y, int *z, int x1, int y1, int x2, int y2)
        vector[Pos3] get_neighbors(int x, int y, int z)

        bool set_point(int x, int y, int z, bool solid, uint32_t color) except +
        void set_column_solid(int x, int y, int z_start, int z_end, bool solid) except +
        void set_column_color(int x, int y, int z_start, int z_end, uint32_t solid) except +

        bool check_node(int x, int y, int z, bool destroy)

    int get_pos(int x, int y, int z)
    bool is_valid_pos(int x, int y, int z)
    bool is_valid_pos(int pos)
    # int check_node(int x, int y, int z, AceMap *map, int destroy)

    enum: MAP_X, MAP_Y, MAP_Z, DEFAULT_COLOR

cdef class VXLMap:
    cdef AceMap *map_data
    cdef public:
        int estimated_size
        str name

    cpdef bint can_build(self, int x, int y, int z)

    cpdef bint set_point(self, int x, int y, int z, bool solid, uint32_t color=?, bool destroy=?)
    # cpdef uint32_t get_color(self, size_t x, size_t y, size_t z)
    # cpdef bint get_solid(self, size_t x, size_t y, size_t z)
    cpdef int get_z(self, int x, int y, int start=?)
    cpdef tuple get_random_pos(self, int x1, int y1, int x2, int y2)
    # cpdef list get_neighbors(self, int x, int y, int z)

    cpdef bytes get_bytes(self)


cdef class VXLMapIterator:
    cdef public:
        VXLMap map
