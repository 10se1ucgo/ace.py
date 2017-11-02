cdef extern from "bytes_c.cpp" nogil:
    uint8_t   read_uint8(char *buffer)
    uint16_t read_uint16(char *buffer)
    uint32_t read_uint32(char *buffer)

    int8_t   read_int8(char *buffer)
    int16_t read_int16(char *buffer)
    int32_t read_int32(char *buffer)

    float read_float(char *buffer)

cdef extern from "<string.h>" nogil:
    size_t strnlen(const char *s, size_t maxlen) # this isn't standard but gcc and msvc implement it so fuck it

cdef class ByteReader:
    def __init__(self, bytes buf, size_t size=0):
        self.buf = buf
        self.start = <char *>buf
        self.pos = self.start

        if size == 0:
            size = len(buf)
            if size == 0:
                raise IOError("No data.")

        self.end = self.start + size

    cdef char *read(self, size_t num) except NULL:
        if self.pos + num > self.end:
            raise IOError("Not enough data left.")

        cdef char *pos = self.pos
        self.pos += num
        return pos

    cpdef uint8_t read_uint8(self) except? 0:
        return read_uint8(self.read(sizeof(uint8_t)))

    cpdef int8_t read_int8(self) except? 0:
        return read_int8(self.read(sizeof(int8_t)))

    cpdef uint16_t read_uint16(self) except? 0:
        return read_uint16(self.read(sizeof(uint16_t)))

    cpdef int16_t read_int16(self) except? 0:
        return read_int16(self.read(sizeof(int16_t)))

    cpdef uint32_t read_uint32(self) except? 0:
        return read_uint32(self.read(sizeof(uint32_t)))

    cpdef int32_t read_int32(self) except? 0:
        return read_int32(self.read(sizeof(int32_t)))

    cpdef float read_float(self) except? 0:
        return read_float(self.read(sizeof(float)))

    cpdef bytes read_bytes(self, size_t length = 0):
        if length == 0:
            length = strnlen(self.pos, self.end - self.pos)
        cdef const char *str = self.read(length + 1)
        return str[:length]

    cpdef bint data_left(self):
        return self.pos != self.end

    cpdef bytes get(self):
        return self.pos[:self.end - self.pos]

    def __len__(self):
        return self.end - self.start

    def __bytes__(self):
        return self.get()

    def __repr__(self):
        return repr(self.get())

cdef class ByteWriter:
    def __cinit__(self):
        self.vec = new vector[char]()

    def __dealloc__(self):
        del self.vec

    cpdef void write(self, bytes data, size_t size=0) except *:
        if size == 0:
            size = len(data)
        self.write_buf(data, size)

    cdef void write_buf(self, char *buf, size_t size) except +:
        self.vec.insert(self.vec.end(), buf, buf + size)

    cpdef void write_uint8(self, uint8_t val) except +:
        self.write_buf(<char *>&val, sizeof(uint8_t))

    cpdef void write_int8(self, int8_t val) except +:
        self.write_buf(<char *>&val, sizeof(int8_t))

    cpdef void write_uint16(self, uint16_t val) except +:
        self.write_buf(<char *>&val, sizeof(uint16_t))

    cpdef void write_int16(self, int16_t val) except +:
        self.write_buf(<char *>&val, sizeof(int16_t))

    cpdef void write_uint32(self, uint32_t val) except +:
        self.write_buf(<char *>&val, sizeof(uint32_t))

    cpdef void write_int32(self, int32_t val) except +:
        self.write_buf(<char *>&val, sizeof(int32_t))

    cpdef void write_float(self, float val) except +:
        self.write_buf(<char *>&val, sizeof(float))

    cpdef void write_bytes(self, bytes val) except +:
        self.write(val + b'\x00')

    cpdef bytes get(self):
        return self.vec.data()[:self.vec.size()]

    def __len__(self):
        return self.vec.size()

    def __bytes__(self):
        return self.get()

    def __repr__(self):
        return repr(self.get())
