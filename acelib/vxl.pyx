# distutils: sources = acelib/vxl_c.cpp
import zlib

VXL_MAP_X = MAP_X
VXL_MAP_Y = MAP_Y
VXL_MAP_Z = MAP_Z
VXL_DEFAULT_COLOR = DEFAULT_COLOR

cdef class VXLMap:
    def __cinit__(self, uint8_t *buffer=NULL):
        self.map_data = new AceMap(buffer)
        self.estimated_size = len(buffer)

    def __dealloc__(self):
        del self.map_data

    def __init__(self, uint8_t *buffer=NULL):
        # just to make my ide happy LUL
        pass

    def __iter__(self):
        cdef:
            int x = 0, y = 0, size
            vector[uint8_t] v
        v.reserve(8192)
        while True:
            size = self.map_data.write(v, &x, &y, 512)
            if not size:
                break
            yield v.data()[:size]
            v.clear()

    def iter_compressed(self):
        cdef int total = 0
        # cdef bytes data

        compressor = zlib.compressobj(9)
        for data in iter(self):
            data = compressor.compress(data)
            total += len(data)
            yield data
        data = compressor.flush()
        self.estimated_size = total + len(data)
        yield data

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
            if self.can_build(node.x, node.y, node.z):
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

    def width(self):
        return MAP_X

    def length(self):
        return MAP_Y

    def depth(self):
        return MAP_Z

    def to_grid(self, x: double, y: double):
        letter = chr(ord('A') + int(x / 64))
        number = str(int(y / 64) + 1)
        return letter + number

    def from_grid(self, grid: str):
        letter = grid[0].lower()
        number = int(grid[1])
        x = max(0, min(self.width() - 1, 32 + (64 * (ord(letter) - ord('a')))))
        y = max(0, min(self.length() - 1, 32 + (64 * (number - 1))))
        return x, y

    def __bytes__(self):
        return self.get_bytes()



