from libcpp cimport bool

cdef extern from "math3d_c.h":
    cdef cppclass Vector3[T]:
        T x, y, z
        Vector3() except +
        Vector3(T x, T y, T z) except +
        Vector3(const Vector3[T] &other) except +

        void set(T x, T y, T z)
        void normalize()

        T sq_magnitude()
        T magnitude()

        T sq_distance(Vector3[T] &other)
        T distance(Vector3[T] &other)
        T dot(Vector3[T] &other)
        double angle(Vector3[T] &other, bool deg)
        bool equals(Vector3[T] &other, T tolerance)

        Vector3[T] cross(Vector3[T] &other)
        Vector3[T] lerp(Vector3[T] &other, double t, bool clamped)
        Vector3[T] scale(Vector3[T] &other)
        Vector3[T] max(Vector3[T] &other)
        Vector3[T] min(Vector3[T] &other)

        Vector3[T] operator+(Vector3[T] &b)
        Vector3[T] operator-(Vector3[T] &b)
        Vector3[T] operator*(T &b)
        Vector3[T] operator/(T &b)

        # Vector3[T] &operator+=(Vector3[T] &b)
        # Vector3[T] &operator-=(Vector3[T] &b)
        # Vector3[T] &operator*=(T &b)
        # Vector3[T] &operator/=(T &b)

        bool operator==(Vector3[T] &b)
        bool operator!=(Vector3[T] &b)
