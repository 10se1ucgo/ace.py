cimport cython

from libc.stdlib cimport malloc, free
from libc.math cimport sin, cos
from libcpp cimport limits


cdef class Vector3:
    def __cinit__(self, double x=0, double y=0, double z=0, bint ref=False):
        if not ref:
            self.c_vec = new math3d_c.Vector3[double](x, y, z)
        self.is_ref = ref

    def __dealloc__(self):
        if not self.is_ref:
            del self.c_vec

    def __init__(self, double x=0, double y=0, double z=0, bint ref=False):
        pass

    def __hash__(self):
        return hash((self.c_vec.x, self.c_vec.y, self.c_vec.z))

    def __len__(self):
        return 3

    def __nonzero__(self):
        return self.c_vec.x != 0 or self.c_vec.y != 0 or self.c_vec.z != 0

    def __add__(Vector3 a, Vector3 b):
        return new_vector3_from(a.c_vec[0] + b.c_vec[0])

    def __sub__(Vector3 a, Vector3 b):
        return new_vector3_from(a.c_vec[0] - b.c_vec[0])

    def __mul__(Vector3 a, double scalar):
        return new_vector3_from(a.c_vec[0] * scalar)

    @cython.cdivision(True)
    def __truediv__(Vector3 a, double scalar):
        if scalar == 0:
            raise ZeroDivisionError("Vector3 division by zero")
        # https://github.com/cython/cython/issues/1950
        # return new_vector3_from(a.c_vec / <double>scalar)
        return new_vector3(a.c_vec.x / scalar, a.c_vec.y / scalar, a.c_vec.z / scalar)

    # No floordiv operator in C++
    @cython.cdivision(True)
    def __floordiv__(Vector3 a, double scalar):
        if scalar == 0:
            raise ZeroDivisionError
        return new_vector3(a.c_vec.x // scalar, a.c_vec.y // scalar, a.c_vec.z // scalar)

    # Cython doesnt support C++ inplace arithmetic operator overloading
    def __iadd__(Vector3 self, Vector3 other):
        self.c_vec.x += other.c_vec.x
        self.c_vec.y += other.c_vec.y
        self.c_vec.z += other.c_vec.z
        return self

    def __isub__(self, Vector3 other):
        self.c_vec.x -= other.c_vec.x
        self.c_vec.y -= other.c_vec.y
        self.c_vec.z -= other.c_vec.z
        return self

    def __imul__(self, double scalar):
        self.c_vec.x *= scalar
        self.c_vec.y *= scalar
        self.c_vec.z *= scalar
        return self

    @cython.cdivision(True)
    def __ifloordiv__(self, double scalar):
        if scalar == 0:
            raise ZeroDivisionError
        self.c_vec.x //= scalar
        self.c_vec.y //= scalar
        self.c_vec.z //= scalar
        return self

    def __eq__(self, Vector3 other):
        return self.c_vec[0] == other.c_vec[0]

    def __neg__(self):
        return new_vector3(-self.c_vec.x, -self.c_vec.y, -self.c_vec.z)

    def __getitem__(self, int key):
        if -3 <= key < 3:
            key %= 3
        else:
            raise IndexError("index out of range")

        cdef double value
        if   key == 0: value = self.c_vec.x
        elif key == 1: value = self.c_vec.y
        elif key == 2: value = self.c_vec.z
        return value

    def __setitem__(self, int key, double value):
        if -3 <= key < 3:
            # augmented assignment doesn't work here, for some reason.
            key %= 3
        else:
            raise IndexError("index out of range")

        if   key == 0: self.c_vec.x = value
        elif key == 1: self.c_vec.y = value
        elif key == 2: self.c_vec.z = value

    def __repr__(self):
        return f"Vector3({self.c_vec.x}, {self.c_vec.y}, {self.c_vec.z})"

    def __copy__(self):
        return new_vector3_from(self.c_vec[0])

    cpdef void set(self, double x, double y, double z):
        self.c_vec.set(x, y, z)

    cpdef void normalize(self):
        self.c_vec.normalize()

    cpdef double sq_magnitude(self):
        return self.c_vec.sq_magnitude()

    cpdef double magnitude(self):
        return self.c_vec.magnitude()

    cpdef double sq_distance(self, Vector3 other):
        return self.c_vec.sq_distance(other.c_vec[0])

    cpdef double distance(self, Vector3 other):
        return self.c_vec.distance(other.c_vec[0])

    cpdef double dot(self, Vector3 other):
        return self.c_vec.dot(other.c_vec[0])

    cpdef double angle(self, Vector3 other, bint deg=True):
        return self.c_vec.angle(other.c_vec[0], deg)

    cpdef bint equals(self, Vector3 other, double tolerance=limits.numeric_limits[double].epsilon()):
        return self.c_vec.equals(other.c_vec[0], tolerance)

    cpdef Vector3 cross(self, Vector3 other):
        return new_vector3_from(self.c_vec.cross(other.c_vec[0]))

    cpdef Vector3 lerp(self, Vector3 other, double t, bint clamped=True):
        return new_vector3_from(self.c_vec.lerp(other.c_vec[0], t, clamped))

    cpdef Vector3 scale(self, Vector3 other):
        return new_vector3_from(self.c_vec.scale(other.c_vec[0]))

    cpdef Vector3 max(self, Vector3 other):
        return new_vector3_from(self.c_vec.max(other.c_vec[0]))

    cpdef Vector3 min(self, Vector3 other):
        return new_vector3_from(self.c_vec.min(other.c_vec[0]))

    @property
    def normalized(self):
        cdef Vector3 ret = new_vector3_from(self.c_vec[0])
        ret.normalize()
        return ret

    @property
    def x(self):
        return self.c_vec.x

    @x.setter
    def x(self, value):
        self.c_vec.x = value

    @property
    def y(self):
        return self.c_vec.y

    @y.setter
    def y(self, value):
        self.c_vec.y = value

    @property
    def z(self):
        return self.c_vec.z

    @z.setter
    def z(self, value):
        self.c_vec.z = value

    @property
    def xyz(self):
        return self.c_vec.x, self.c_vec.y, self.c_vec.z

    @xyz.setter
    def xyz(self, value):
        self.c_vec.x, self.c_vec.y, self.c_vec.z = value

    @staticmethod
    def zero():
        return new_vector3(0, 0, 0)

    @staticmethod
    def one():
        return new_vector3(1, 1, 1)

    @staticmethod
    def forward():
        return new_vector3(0, 1, 0)

    @staticmethod
    def back():
        return new_vector3(0, -1, 0)

    @staticmethod
    def up():
        return new_vector3(0, 0, -1)

    @staticmethod
    def down():
        return new_vector3(0, 0, 1)

    @staticmethod
    def left():
        return new_vector3(-1, 0, 0)

    @staticmethod
    def right():
        return new_vector3(1, 0, 0)


# i wrote this a while back, its probably not very clean or good
cdef class Matrix4x4:
    def __cinit__(self):
        self.as_array = <double**>malloc(16 * sizeof(double*))
        if self.as_array == NULL:
            raise MemoryError

    def __dealloc__(self):
        free(self.as_array)

    def __init__(self,
                 double a=0, double b=0, double c=0, double d=0,
                 double e=0, double f=0, double g=0, double h=0,
                 double i=0, double j=0, double k=0, double l=0,
                 double m=0, double n=0, double o=0, double p=0):
        self.a = a; self.b = b; self.c = c; self.d = d
        self.e = e; self.f = f; self.g = g; self.h = h
        self.i = i; self.j = j; self.k = k; self.l = l
        self.m = m; self.n = n; self.o = o; self.p = p

        self.as_array[0]  = &self.a
        self.as_array[1]  = &self.b
        self.as_array[2]  = &self.c
        self.as_array[3]  = &self.d
        self.as_array[4]  = &self.e
        self.as_array[5]  = &self.f
        self.as_array[6]  = &self.g
        self.as_array[7]  = &self.h
        self.as_array[8]  = &self.i
        self.as_array[9]  = &self.j
        self.as_array[10] = &self.k
        self.as_array[11] = &self.l
        self.as_array[12] = &self.m
        self.as_array[13] = &self.n
        self.as_array[14] = &self.o
        self.as_array[15] = &self.p

    def __repr__(Matrix4x4 self):
        return f"""Matrix4x4([{self.a:.3f}, {self.b:.3f}, {self.c:.3f}, {self.d:.3f},
           {self.e:.3f}, {self.f:.3f}, {self.g:.3f}, {self.h:.3f},
           {self.i:.3f}, {self.j:.3f}, {self.k:.3f}, {self.l:.3f},
           {self.m:.3f}, {self.n:.3f}, {self.o:.3f}, {self.p:.3f}])"""

    def __mul__(a, b):
        cdef double s
        if isinstance(b, Vector3):
            return mat4x4_mul_vec3(a, <Vector3>b)
        elif isinstance(b, Matrix4x4):
            return mat4x4_mul_mat4x4(a, <Matrix4x4>b)
        elif isinstance(b, (int, float)):
            s = <double>b
            return new_mat4x4(a.a * s, a.b * s, a.c * s, a.d * s,
                              a.e * s, a.f * s, a.g * s, a.h * s,
                              a.i * s, a.j * s, a.k * s, a.l * s,
                              a.m * s, a.n * s, a.o * s, a.p * s)
        else:
            raise TypeError("unsupported operand type(s) for *: 'Matrix4x4' and '" + b.__name__ + "'")

    def __imul__(self, b):
        cdef double s
        cdef int x
        if isinstance(b, Matrix4x4):
            mat4x4_mul_mat4x4_inplace(self, <Matrix4x4>b)
        elif isinstance(b, (int, float)):
            s = <double>b
            for x in range(16):
                self.as_array[x][0] *= s
        return self

    def __iter__(self):
        cdef int x
        for x in range(16):
            yield self.as_array[x][0]

    def __getitem__(self, tuple key):
        # slicing not supported
        cdef int item
        if isinstance(key, tuple):
            item = get_index(key)
        else:
            item = <int>key

        return self.as_array[item][0]

    def __setitem__(self, key, double value):
        cdef int item
        if isinstance(key, tuple):
            item = get_index(key)
        else:
            item = <int>key

        self.as_array[item][0] = value

    def get_col(self, int col):
        if -4 <= col < 4:
            col %= 4
        else:
            raise IndexError("col index out of range")

        return (self.as_array[col + 0 * 4][0], self.as_array[col + 1 * 4][0],
                self.as_array[col + 2 * 4][0], self.as_array[col + 3 * 4][0])

    def set_col(Matrix4x4 self, int col, double[:] values not None):
        if -4 <= col < 4:
            col %= 4
        else:
            raise IndexError("row index out of range")

        self.as_array[col + 0 * 4][0] = values[0]
        self.as_array[col + 1 * 4][0] = values[1]
        self.as_array[col + 2 * 4][0] = values[2]
        self.as_array[col + 3 * 4][0] = values[3]

    def get_row(Matrix4x4 self, int row):
        if -4 <= row < 4:
            row %= 4
        else:
            raise IndexError("row index out of range")

        return (self.as_array[0 + row * 4][0], self.as_array[1 + row * 4][0],
                self.as_array[2 + row * 4][0], self.as_array[3 + row * 4][0])

    def set_row(Matrix4x4 self, int row, double[:] values not None):
        if -4 <= row < 4:
            row %= 4
        else:
            raise IndexError("row index out of range")

        self.as_array[0 + row * 4][0] = values[0]
        self.as_array[1 + row * 4][0] = values[1]
        self.as_array[2 + row * 4][0] = values[2]
        self.as_array[3 + row * 4][0] = values[3]

    def set_identity(self):
        self.a = 1; self.b = 0; self.c = 0; self.d = 0
        self.e = 0; self.f = 1; self.g = 0; self.h = 0
        self.i = 0; self.j = 0; self.k = 1; self.l = 0
        self.m = 0; self.n = 0; self.o = 0; self.p = 1

    @staticmethod
    def scale(Vector3 v):
        """
        Creates a scaling matrix

        Args:
            v (Vector3)

        Returns:
            Matrix4x4
        """
        return new_mat4x4(v.x, 0, 0, 0,
                          0, v.y, 0, 0,
                          0, 0, v.z, 0,
                          0, 0, 0, 1.0)

    @staticmethod
    def rotate(double angle, Vector3 axis):
        cdef Vector3 v = axis.normalized
        cdef:
            double c = cos(angle)
            double s = sin(angle)
            Vector3 t = v * (1 - c)

            double vx = v.x
            double vy = v.y
            double vz = v.z

            double tx = t.x
            double ty = t.y
            double tz = t.z

        cdef Matrix4x4 mat = new_mat4x4(1, 0, 0, 0,
                                        0, 1, 0, 0,
                                        0, 0, 1, 0,
                                        0, 0, 0, 1)
        mat.a = c + tx * vx
        mat.b = tx * vy + s * vz
        mat.c = tx * vz - s * vy

        mat.e = ty * vx - s * vz
        mat.f = c + ty * vy
        mat.g = ty * vz + s * vx

        mat.i = tz * vx + s * vy
        mat.j = tz * vy - s * vx
        mat.k = c + tz * vz
        return mat

    @staticmethod
    def identity():
        return new_mat4x4(1, 0, 0, 0,
                          0, 1, 0, 0,
                          0, 0, 1, 0,
                          0, 0, 0, 1)

    @staticmethod
    def zero():
        return new_mat4x4(0, 0, 0, 0,
                          0, 0, 0, 0,
                          0, 0, 0, 0,
                          0, 0, 0, 0)


cdef inline int get_index(tuple key):
    cdef int row, col
    row = key[0]
    col = key[1]
    if -4 <= row < 4:
        row %= 4
    else:
        raise IndexError("row index out of range")

    if -4 <= col < 4:
        col %= 4
    else:
        raise IndexError("column index out of range")
    return row + col * 4


cdef inline Vector3 mat4x4_mul_vec3(Matrix4x4 a, Vector3 b):
    # transform direction b with matrix a.
    cdef:
        double x = b.x
        double y = b.y
        double z = b.z
    return new_vector3(a.a * x + a.b * y + a.c * z,
                       a.e * x + a.f * y + a.g * z,
                       a.i * x + a.j * y + a.k * z)

cdef inline Matrix4x4 mat4x4_mul_mat4x4(Matrix4x4 a, Matrix4x4 b):
    cdef:
        double aa, ab, ac, ad, ae, af, ag, ah, ai, aj, ak, al, am, an, ao, ap, \
               ba, bb, bc, bd, be, bf, bg, bh, bi, bj, bk, bl, bm, bn, bo, bp

    # apparently, you can't use semi-colons in a cdef block to separate statements, so the definition and assignment
    # has to be done outside the block.
    aa = a.a; ab = a.b; ac = a.c; ad = a.d
    ae = a.e; af = a.f; ag = a.g; ah = a.h
    ai = a.i; aj = a.j; ak = a.k; al = a.l
    am = a.m; an = a.n; ao = a.o; ap = a.p

    ba = b.a; bb = b.b; bc = b.c; bd = b.d
    be = b.e; bf = b.f; bg = b.g; bh = b.h
    bi = b.i; bj = b.j; bk = b.k; bl = b.l
    bm = b.m; bn = b.n; bo = b.o; bp = b.p

    return new_mat4x4(aa * ba + ab * be + ac * bi + ad * bm,
                      aa * bb + ab * bf + ac * bj + ad * bn,
                      aa * bc + ab * bg + ac * bk + ad * bo,
                      aa * bd + ab * bh + ac * bl + ad * bp,
                      ae * ba + af * be + ag * bi + ah * bm,
                      ae * bb + af * bf + ag * bj + ah * bn,
                      ae * bc + af * bg + ag * bk + ah * bo,
                      ae * bd + af * bh + ag * bl + ah * bp,
                      ai * ba + aj * be + ak * bi + al * bm,
                      ai * bb + aj * bf + ak * bj + al * bn,
                      ai * bc + aj * bg + ak * bk + al * bo,
                      ai * bd + aj * bh + ak * bl + al * bp,
                      am * ba + an * be + ao * bi + ap * bm,
                      am * bb + an * bf + ao * bj + ap * bn,
                      am * bc + an * bg + ao * bk + ap * bo,
                      am * bd + an * bh + ao * bl + ap * bp)

# todo combine this
cdef inline void mat4x4_mul_mat4x4_inplace(Matrix4x4 a, Matrix4x4 b):
    cdef:
        double aa, ab, ac, ad, ae, af, ag, ah, ai, aj, ak, al, am, an, ao, ap, \
               ba, bb, bc, bd, be, bf, bg, bh, bi, bj, bk, bl, bm, bn, bo, bp

    aa = a.a; ab = a.b; ac = a.c; ad = a.d
    ae = a.e; af = a.f; ag = a.g; ah = a.h
    ai = a.i; aj = a.j; ak = a.k; al = a.l
    am = a.m; an = a.n; ao = a.o; ap = a.p

    ba = b.a; bb = b.b; bc = b.c; bd = b.d
    be = b.e; bf = b.f; bg = b.g; bh = b.h
    bi = b.i; bj = b.j; bk = b.k; bl = b.l
    bm = b.m; bn = b.n; bo = b.o; bp = b.p

    a.a = aa * ba + ab * be + ac * bi + ad * bm
    a.b = aa * bb + ab * bf + ac * bj + ad * bn
    a.c = aa * bc + ab * bg + ac * bk + ad * bo
    a.d = aa * bd + ab * bh + ac * bl + ad * bp
    a.e = ae * ba + af * be + ag * bi + ah * bm
    a.f = ae * bb + af * bf + ag * bj + ah * bn
    a.g = ae * bc + af * bg + ag * bk + ah * bo
    a.h = ae * bd + af * bh + ag * bl + ah * bp
    a.i = ai * ba + aj * be + ak * bi + al * bm
    a.j = ai * bb + aj * bf + ak * bj + al * bn
    a.k = ai * bc + aj * bg + ak * bk + al * bo
    a.l = ai * bd + aj * bh + ak * bl + al * bp
    a.m = am * ba + an * be + ao * bi + ap * bm
    a.n = am * bb + an * bf + ao * bj + ap * bn
    a.o = am * bc + an * bg + ao * bk + ap * bo
    a.p = am * bd + an * bh + ao * bl + ap * bp
