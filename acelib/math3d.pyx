cimport cython
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
