# distutils: sources = acelib/vxl_c.cpp
VXL_MAP_X = MAP_X
VXL_MAP_Y = MAP_Y
VXL_MAP_Z = MAP_Z
VXL_DEFAULT_COLOR = DEFAULT_COLOR

cdef class VXLMap:
    def __cinit__(self, uint8_t *buffer=NULL):
        self.map_data = new AceMap(buffer)

    def __dealloc__(self):
        del self.map_data

    def __init__(self, uint8_t *buffer=NULL):
        # just to make my ide happy LUL
        pass

    cpdef bint can_build(self, int x, int y, int z):
        return x < MAP_X and y < MAP_Y and z < MAP_Z - 2
        # if not x < MAP_X and y < MAP_Y and z < MAP_Z - 2:
        #     return False
        # cdef vector[Pos3] neighbors = self.map_data.get_neighbors(x, y, z)
        # print(neighbors.capacity())
        # return not neighbors.empty()

    cpdef bint set_point(self, int x, int y, int z, bool solid, uint32_t color=0, bool destroy=True):
        cdef bint ok = self.map_data.set_point(x, y, z, solid, color)
        if not destroy:
            return ok

        cdef vector[Pos3] neighbors = self.map_data.get_neighbors(x, y, z)
        cdef Pos3 node
        for node in neighbors:
            if node.z < 62:
                self.map_data.check_node(node.x, node.y, node.z, True)
        return ok

    cpdef int get_z(self, int x, int y, int start = 0):
        return self.map_data.get_z(x, y, start)

    cpdef tuple get_random_pos(self, int x1, int y1, int x2, int y2):
        cdef int x, y, z
        self.map_data.get_random_point(&x, &y, &z, x1, y1, x2, y2)
        return x, y, z

    cpdef bytes get_bytes(self):
        cdef vector[uint8_t] x = self.map_data.write()
        return x.data()[:x.size()]

    def __bytes__(self):
        return self.get_bytes()






