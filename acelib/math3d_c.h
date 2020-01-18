#pragma once
#include <cmath>
#include <algorithm>
#include <iostream>

// TODO: Replace with glm
// TODO: Replace Cython with pybind11 :flushed:

namespace detail {
    template<typename T>
    T magnitude3(T x, T y, T z) {
        return std::pow(x, 2) + std::pow(y, 2) + std::pow(z, 2);
    }

    template<typename T>
    const T &clamp(const T &x, const T &upper, const T &lower) {
        return std::min(upper, std::max(x, lower));
    }

    template<typename T>
    bool close_enough(const T &first, const T &second, T tolerance) {
        return std::abs(first - second) <= tolerance;
    }

    constexpr double PI = 3.14159265358979323846;
}


template<typename T>
struct Vector3 {
    T x, y, z;

    explicit Vector3(T x=0, T y=0, T z=0) : x(x), y(y), z(z) {
    }

    void set(T x, T y, T z);
    void normalize();

    T sq_magnitude() const;
    T magnitude() const;

    T sq_distance(const Vector3<T> &other) const;
    T distance(const Vector3<T> &other) const;
    T dot(const Vector3<T> &other) const;
    double angle(const Vector3<T> &other, bool deg=true) const;
    bool equals(const Vector3<T> &other, T tolerance = std::numeric_limits<T>::epsilon());

    Vector3<T> cross(const Vector3<T> &other) const;
    Vector3<T> lerp(const Vector3<T> &other, double t, bool clamped=true) const;
    Vector3<T> scale(const Vector3<T> &other) const;
    Vector3<T> max(const Vector3<T> &other) const;
    Vector3<T> min(const Vector3<T> &other) const;

    Vector3<T> operator+(const Vector3<T> &b) const;
    Vector3<T> operator-(const Vector3<T> &b) const;
    Vector3<T> operator*(const T &b) const;
    Vector3<T> operator/(const T &b) const;

    Vector3<T> &operator+=(const Vector3<T> &b);
    Vector3<T> &operator-=(const Vector3<T> &b);
    Vector3<T> &operator*=(const T &b);
    Vector3<T> &operator/=(const T &b);

    bool operator==(const Vector3<T> &b) const;
    bool operator!=(const Vector3<T> &b) const;
};

template<typename T>
void Vector3<T>::set(T x, T y, T z) {
    this->x = x; this->y = y; this->z = z;
}

template<typename T>
void Vector3<T>::normalize() {
    T mag = this->magnitude();
    if(mag > 0) {
        this->x /= mag; this->y /= mag; this->z /= mag;
    } else {
        this->x = this->y = this->z = 0;
    }
}

template<typename T>
T Vector3<T>::sq_magnitude() const {
    return detail::magnitude3(this->x, this->y, this->z);
}

template<typename T>
T Vector3<T>::magnitude() const {
    return std::sqrt(this->sq_magnitude()); 
}

template<typename T>
T Vector3<T>::sq_distance(const Vector3<T> &other) const {
    return detail::magnitude3(this->x - other.x, this->y - other.y, this->z - other.z);
}

template<typename T>
T Vector3<T>::distance(const Vector3<T> &other) const {
    return std::sqrt(this->sq_distance(other));
}

template<typename T>
T Vector3<T>::dot(const Vector3<T> &other) const {
    return this->x * other.x +
           this->y * other.y +
           this->z * other.z;
}

template<typename T>
double Vector3<T>::angle(const Vector3<T> &other, bool deg) const {
    double x = std::acos(detail::clamp<T>(this->dot(other), 1.0, -1.0));
    return deg ? x * (180.0 / detail::PI) : x;
}

template<typename T>
bool Vector3<T>::equals(const Vector3<T> &other, T tolerance) {
    return detail::close_enough(this->x, other.x, tolerance) &&
           detail::close_enough(this->y, other.y, tolerance) &&
           detail::close_enough(this->z, other.z, tolerance);
}

template<typename T>
Vector3<T> Vector3<T>::cross(const Vector3<T> &other) const {
    return Vector3<T>(this->y * other.z - this->z * other.y,
                      this->z * other.x - this->x * other.z,
                      this->x * other.y - this->y * other.x);
}

template<typename T>
Vector3<T> Vector3<T>::lerp(const Vector3<T> &other, double t, bool clamped) const {
    t = clamped ? detail::clamp(t, 1.0, 0.0) : t;
    if(t == 1.0)
        return other;
    if (t == 0.0)
        return *this;

    return Vector3<T>(this->x + (other.x - this->x) * t,
                      this->y + (other.y - this->y) * t,
                      this->z + (other.z - this->z) * t);
}

template<typename T>
Vector3<T> Vector3<T>::scale(const Vector3<T> &other) const {
    return Vector3<T>(this->x * other.x,
                      this->y * other.y,
                      this->z * other.z);
}

template<typename T>
Vector3<T> Vector3<T>::max(const Vector3<T> &other) const {
    return Vector3<T>(std::max(this->x, other.x),
                      std::max(this->y, other.y),
                      std::max(this->z, other.z));
}

template<typename T>
Vector3<T> Vector3<T>::min(const Vector3<T> &other) const {
    return Vector3<T>(std::min(this->x, other.x),
                      std::min(this->y, other.y),
                      std::min(this->z, other.z));
}

template<typename T>
Vector3<T> Vector3<T>::operator+(const Vector3<T> &b) const {
    return Vector3(this->x + b.x, this->y + b.y, this->z + b.z);
}

template<typename T>
Vector3<T> Vector3<T>::operator-(const Vector3<T> &b) const {
    return Vector3(this->x - b.x, this->y - b.y, this->z - b.z);
}

template<typename T>
Vector3<T> Vector3<T>::operator*(const T &b) const {
    return Vector3(this->x * b, this->y * b, this->z * b);
}

template<typename T>
Vector3<T> Vector3<T>::operator/(const T &b) const {
    return Vector3(this->x / b, this->y / b, this->z / b);
}

template<typename T>
Vector3<T> &Vector3<T>::operator+=(const Vector3<T> &b) {
    this->x += b.x; this->y += b.y; this->z += b.z;
    return *this;
}

template<typename T>
Vector3<T> &Vector3<T>::operator-=(const Vector3<T> &b) {
    this->x -= b.x; this->y -= b.y; this->z -= b.z;
    return *this;
}

template<typename T>
Vector3<T>& Vector3<T>::operator*=(const T &b) {
    this->x *= b; this->y *= b; this->z *= b;
    return *this;
}

template<typename T>
Vector3<T>& Vector3<T>::operator/=(const T &b) {
    this->x /= b; this->y /= b; this->z /= b;
    return *this;
}

template<typename T>
bool Vector3<T>::operator==(const Vector3<T> &b) const {
    return (this->x == b.x && this->y == b.y && this->z == b.z);
}

template<typename T>
bool Vector3<T>::operator!=(const Vector3<T> &b) const {
    return !(this->operator==(b));
}
