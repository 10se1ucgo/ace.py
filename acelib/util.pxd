from libc.stdint cimport *

from .bytes cimport ByteReader, ByteWriter


cdef inline void read_position(ByteReader reader, float *x, float *y, float *z):
    x[0] = reader.read_float()
    y[0] = reader.read_float()
    z[0] = reader.read_float()

cdef inline void write_position(ByteWriter writer, float x, float y, float z):
    writer.write_float(x)
    writer.write_float(y)
    writer.write_float(z)

cdef inline void read_color(ByteReader reader, uint8_t *r, uint8_t *g, uint8_t *b):
    b[0] = reader.read_uint8()
    g[0] = reader.read_uint8()
    r[0] = reader.read_uint8()

cdef inline void write_color(ByteWriter writer, uint8_t r, uint8_t g, uint8_t b):
    writer.write_uint8(b)
    writer.write_uint8(g)
    writer.write_uint8(r)
