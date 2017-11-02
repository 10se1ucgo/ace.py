#include <stdint.h>

// because cython's libcpp.cast.reinterpret_cast[T] doesn't like to play well with pointer types.
// [because template functions dont play well with pointer types(?) https://github.com/cython/cython/issues/534]

inline uint8_t read_uint8(char *buffer) {
    return *reinterpret_cast<uint8_t *>(buffer);
}

inline int8_t read_int8(char *buffer) {
    return *reinterpret_cast<int8_t *>(buffer);
}

inline uint16_t read_uint16(char *buffer) {
    return *reinterpret_cast<uint16_t *>(buffer);
}

inline int16_t read_int16(char *buffer) {
    return *reinterpret_cast<int16_t *>(buffer);
}

inline uint32_t read_uint32(char *buffer) {
    return *reinterpret_cast<uint32_t *>(buffer);
}

inline int32_t read_int32(char *buffer) {
    return *reinterpret_cast<int32_t *>(buffer);
}

inline float read_float(char *buffer) {
    return *reinterpret_cast<float *>(buffer);
}
