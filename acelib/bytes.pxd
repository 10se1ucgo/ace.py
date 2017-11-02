from libc.stdint cimport *
from libcpp.vector cimport vector

cdef class ByteReader:
    cdef:
        bytes buf # keep a reference to the Python bytes or else it'll be garbage collected
        char *start
        char *pos
        char *end

    cdef char *read(self, size_t num) except NULL
    cpdef uint8_t read_uint8(self) except? 0
    cpdef int8_t read_int8(self) except? 0
    cpdef uint16_t read_uint16(self) except? 0
    cpdef int16_t read_int16(self) except? 0
    cpdef uint32_t read_uint32(self) except? 0
    cpdef int32_t read_int32(self) except? 0
    cpdef float read_float(self) except? 0
    cpdef bytes read_bytes(self, size_t length = *)
    cpdef bint data_left(self)
    cpdef bytes get(self)

cdef class ByteWriter:
    cdef vector[char] *vec

    cpdef void write(self, bytes data, size_t size = ?) except *
    cdef  void write_buf(self, char *buf, size_t size) except +
    cpdef void write_uint8(self, uint8_t val) except +
    cpdef void write_int8(self, int8_t val) except +
    cpdef void write_uint16(self, uint16_t val) except +
    cpdef void write_int16(self, int16_t val) except +
    cpdef void write_uint32(self, uint32_t val) except +
    cpdef void write_int32(self, int32_t val) except +
    cpdef void write_float(self, float val) except +
    cpdef void write_bytes(self, bytes val) except +
    cpdef bytes get(self)
