#include <cmath>

#include "vxl_c.h"
#include "math3d_c.h"

constexpr float FALL_SLOW_DOWN = 0.24f;
constexpr float FALL_DAMAGE_VELOCITY = 0.58f;
constexpr int FALL_DAMAGE_SCALAR = 4096;

typedef Vector3<double> Vector;

struct Orientation {
    Vector f, s, h;
};

struct AcePlayer {
    explicit AcePlayer(AceMap *map): f(1, 0, 0), s(0, 1, 0), h(0, 0, 1) {
        this->map = map;
        this->mf = this->mb = this->ml = this->mr = false;
        this->jump = this->crouch = this->sneak = this->sprint = false;
        this->primary_fire = this->secondary_fire = this->weapon = false;
        this->airborne = this->wade = false;
        this->alive = true;
        this->lastclimb = 0.0;
    }
    long update(double dt, double time);
    void set_orientation(double x, double y, double z);

    AceMap *map;
    bool mf, mb, ml, mr, jump, crouch, sneak, sprint, primary_fire, secondary_fire, airborne, wade, alive, weapon;
    double lastclimb;
    Vector p, e, v, f, s, h;

private:
    void boxclipmove(double dt, double time);
    void reposition(double dt, double time);
};

struct AceGrenade {
    AceGrenade(AceMap *map, Vector position, Vector velocity) : map(map), p(position), v(velocity) {
    }
    AceGrenade(AceMap *map, double px, double py, double pz, double vx, double vy, double vz) : map(map), p(px, py, pz), v(vx, vy, vz) {
    }
    bool update(double dt, double time);

    AceMap *map;
    Vector p, v;
};

// should these be methods on AceMap ?
//same as isvoxelsolid but water is empty && out of bounds returns true
bool clipbox(AceMap *map, float x, float y, float z)
{
    if (x < 0 || x >= MAP_X || y < 0 || y >= MAP_Y)
        return true;
    if (z < 0)
        return false;

    int sz = z;
    if (sz == MAP_Z - 1)
        sz -= 1;
    else if (sz >= MAP_Z)
        return true;
    return map->get_solid(x, y, sz);
}

//same as isvoxelsolid but water is empty
bool clipworld(AceMap *map, long x, long y, long z)
{
    if (x < 0 || x >= MAP_X || y < 0 || y >= MAP_Y)
        return false;
    if (z < 0)
        return false;

    int sz = z;
    if (sz == 63)
        sz = 62;
    else if (sz >= 63)
        return true;
    else if (sz < 0)
        return false;
    return map->get_solid(x, y, sz);
}

long AcePlayer::update(double dt, double time) {
    //move player and perform simple physics (gravity, momentum, friction)
    if (this->jump)
    {
        this->jump = false;
        this->v.z = -0.36f;
    }

    float f = dt; //player acceleration scalar
    if (this->airborne)
        f *= 0.1f;
    else if (this->crouch)
        f *= 0.3f;
    else if ((this->secondary_fire && this->weapon) || this->sneak)
        f *= 0.5f;
    else if (this->sprint)
        f *= 1.3f;

    if ((this->mf || this->mb) && (this->ml || this->mr))
        f *= sqrt(0.5); //if strafe + forward/backwards then limit diagonal velocity

    if (this->mf)
    {
        this->v.x += this->f.x*f;
        this->v.y += this->f.y*f;
    }
    else if (this->mb)
    {
        this->v.x -= this->f.x*f;
        this->v.y -= this->f.y*f;
    }
    if (this->ml)
    {
        this->v.x -= this->s.x*f;
        this->v.y -= this->s.y*f;
    }
    else if (this->mr)
    {
        this->v.x += this->s.x*f;
        this->v.y += this->s.y*f;
    }

    f = dt + 1;
    this->v.z += dt;
    this->v.z /= f; //air friction
    if (this->wade)
        f = dt*6.f + 1; //water friction
    else if (!this->airborne)
        f = dt*4.f + 1; //ground friction
    this->v.x /= f;
    this->v.y /= f;
    float f2 = this->v.z;
    this->boxclipmove(dt, time);
    //hit ground... check if hurt
    if (!this->v.z && (f2 > FALL_SLOW_DOWN))
    {
        //slow down on landing
        this->v.x *= 0.5f;
        this->v.y *= 0.5f;

        //return fall damage
        if (f2 > FALL_DAMAGE_VELOCITY)
        {
            f2 -= FALL_DAMAGE_VELOCITY;
            return f2 * f2 * FALL_DAMAGE_SCALAR;
        }

        return -1; // no fall damage but play fall sound
    }

    return 0; //no fall damage
}

void AcePlayer::set_orientation(double x, double y, double z) {
    float f = sqrtf(x*x + y*y);
    this->f.set(x, y, z);
    this->s.set(-y / f, x / f, 0.0);
    this->h.set(-z * this->s.y, z * this->s.x, (x * this->s.y) - (y * this->s.x));
}

void AcePlayer::boxclipmove(double dt, double time) {
    float offset, m;
    if (this->crouch)
    {
        offset = 0.45f;
        m = 0.9f;
    }
    else
    {
        offset = 0.9f;
        m = 1.35f;
    }

    float f = dt * 32.f;
    float nx = f * this->v.x + this->p.x;
    float ny = f * this->v.y + this->p.y;
    float nz = this->p.z + offset;

    bool climb = false;
    if (this->v.x < 0) f = -0.45f;
    else f = 0.45f;
    float z = m;
    while (z >= -1.36f && !clipbox(this->map, nx + f, this->p.y - 0.45f, nz + z) && !clipbox(this->map, nx + f, this->p.y + 0.45f, nz + z))
        z -= 0.9f;
    if (z<-1.36f) this->p.x = nx;
    else if (!this->crouch && this->f.z<0.5f && !this->sprint)
    {
        z = 0.35f;
        while (z >= -2.36f && !clipbox(this->map, nx + f, this->p.y - 0.45f, nz + z) && !clipbox(this->map, nx + f, this->p.y + 0.45f, nz + z))
            z -= 0.9f;
        if (z<-2.36f)
        {
            this->p.x = nx;
            climb = true;
        }
        else this->v.x = 0;
    }
    else this->v.x = 0;

    if (this->v.y < 0) f = -0.45f;
    else f = 0.45f;
    z = m;
    while (z >= -1.36f && !clipbox(this->map, this->p.x - 0.45f, ny + f, nz + z) && !clipbox(this->map, this->p.x + 0.45f, ny + f, nz + z))
        z -= 0.9f;
    if (z<-1.36f) this->p.y = ny;
    else if (!this->crouch && this->f.z<0.5f && !this->sprint && !climb)
    {
        z = 0.35f;
        while (z >= -2.36f && !clipbox(this->map, this->p.x - 0.45f, ny + f, nz + z) && !clipbox(this->map, this->p.x + 0.45f, ny + f, nz + z))
            z -= 0.9f;
        if (z<-2.36f)
        {
            this->p.y = ny;
            climb = true;
        }
        else this->v.y = 0;
    }
    else if (!climb)
        this->v.y = 0;

    if (climb)
    {
        this->v.x *= 0.5f;
        this->v.y *= 0.5f;
        this->lastclimb = time;
        nz--;
        m = -1.35f;
    }
    else
    {
        if (this->v.z < 0)
            m = -m;
        nz += this->v.z*dt*32.f;
    }

    this->airborne = true;

    if (clipbox(this->map, this->p.x - 0.45f, this->p.y - 0.45f, nz + m) ||
        clipbox(this->map, this->p.x - 0.45f, this->p.y + 0.45f, nz + m) ||
        clipbox(this->map, this->p.x + 0.45f, this->p.y - 0.45f, nz + m) ||
        clipbox(this->map, this->p.x + 0.45f, this->p.y + 0.45f, nz + m))
    {
        if (this->v.z >= 0)
        {
            this->wade = this->p.z > 61;
            this->airborne = false;
        }
        this->v.z = 0;
    }
    else
        this->p.z = nz - offset;

    this->reposition(dt, time);
}

void AcePlayer::reposition(double dt, double time) {
    this->e.set(this->p.x, this->p.y, this->p.z);
    double f = this->lastclimb - time; /* FIXME meaningful name */
    if (f>-0.25f)
        this->e.z += (f + 0.25f) / 0.25f;
}

bool AceGrenade::update(double dt, double time) {
    Vector fpos = this->p; //old position

    //do velocity & gravity (friction is negligible)
    float f = dt * 32;
    this->v.z += dt;
    // yikes, my vector type operator overloading actually has a use!!!
    this->p += this->v * f;

    //make it bounce (accurate)
    Vector3<long> lp(floor(this->p.x), floor(this->p.y), floor(this->p.z));

    if (clipworld(this->map, lp.x, lp.y, lp.z)) { //hit a wall
        Vector3<long> lp2(floor(fpos.x), floor(fpos.y), floor(fpos.z));
        if (lp.z != lp2.z && ((lp.x == lp2.x && lp.y == lp2.y) || !clipworld(this->map, lp.x, lp.y, lp2.z)))
            this->v.z = -this->v.z;
        else if (lp.x != lp2.x && ((lp.y == lp2.y && lp.z == lp2.z) || !clipworld(this->map, lp2.x, lp.y, lp.z)))
            this->v.x = -this->v.x;
        else if (lp.y != lp2.y && ((lp.x == lp2.x && lp.z == lp2.z) || !clipworld(this->map, lp.x, lp2.y, lp.z)))
            this->v.y = -this->v.y;

        this->p = fpos; //set back to old position
        this->v *= 0.36;
        return true;
    }
    return false;
}

bool cast_ray(AceMap *map, const Vector &position, const Vector &direction, long *x, long *y, long *z, float length=32, bool isdirection=true) {
    double x0 = position.x; double y0 = position.y; double z0 = position.z;
    double x1 = direction.x; double y1 = direction.y; double z1 = direction.z;

    if (isdirection) {
        x1 = x0 + x1 * length;
        y1 = y0 + y1 * length;
        z1 = z0 + z1 * length;
    }

    Vector f, g;
    Vector3<long> a, c, d, p, i;
    long cnt = 0;

    a.set(x0 - .5, y0 - .5, z0 - .5);
    c.set(x1 - .5, y1 - .5, z1 - .5);

    if (c.x <  a.x) {
        d.x = -1; f.x = x0 - a.x; g.x = (x0 - x1) * 1024; cnt += a.x - c.x;
    }
    else if (c.x != a.x) {
        d.x = 1; f.x = a.x + 1 - x0; g.x = (x1 - x0) * 1024; cnt += c.x - a.x;
    }
    else
        f.x = g.x = 0;
    if (c.y <  a.y) {
        d.y = -1; f.y = y0 - a.y;   g.y = (y0 - y1) * 1024; cnt += a.y - c.y;
    }
    else if (c.y != a.y) {
        d.y = 1; f.y = a.y + 1 - y0; g.y = (y1 - y0) * 1024; cnt += c.y - a.y;
    }
    else
        f.y = g.y = 0;
    if (c.z <  a.z) {
        d.z = -1; f.z = z0 - a.z;   g.z = (z0 - z1) * 1024; cnt += a.z - c.z;
    }
    else if (c.z != a.z) {
        d.z = 1; f.z = a.z + 1 - z0; g.z = (z1 - z0) * 1024; cnt += c.z - a.z;
    }
    else
        f.z = g.z = 0;

    p.set(f.x*g.z - f.z*g.x,
          f.y*g.z - f.z*g.y,
          f.y*g.x - f.x*g.y);
    i.set(g.x, g.y, g.z);

    if (cnt > length)
        cnt = length;
    while (cnt)
    {
        if (((p.x | p.y) >= 0) && (a.z != c.z)) {
            a.z += d.z; p.x -= i.x; p.y -= i.y;
        }
        else if ((p.z >= 0) && (a.x != c.x)) {
            a.x += d.x; p.x += i.z; p.z -= i.y;
        }
        else {
            a.y += d.y; p.y += i.z; p.z += i.x;
        }

        if (map->get_solid(a.x, a.y, a.z, true)) {
            *x = a.x;
            *y = a.y;
            *z = a.z;
            return true;
        }
        cnt--;
    }
    return false;
}


//inline void get_orientation(Orientation * o, float x, float y, float z) {
//    float f = sqrtf(x*x + y*y);
//    o->f.set(x, y, z);
//    o->s.set(-y / f, x / f, 0.0);
//    o->h.set(-z * o->s.y, z * o->s.x, (x * o->s.y) - (y * o->s.x));
//}
//
//
//inline void set_orientation_vectors(float x, float y, float z, Vector * s, Vector * h)
//{
//    float f = sqrtf(x*x + y*y);
//    s->x = -y / f;
//    s->y = x / f;
//    h->x = -z*s->y;
//    h->y = z*s->x;
//    h->z = x*s->y - y*s->x;
//}
