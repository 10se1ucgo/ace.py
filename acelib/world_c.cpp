#include <cmath>

#include "vxl_c.h"
#include "math3d_c.h"

constexpr float FALL_SLOW_DOWN = 0.24f;
constexpr float FALL_DAMAGE_VELOCITY = 0.58f;
constexpr int FALL_DAMAGE_SCALAR = 4096;

typedef Vector3<double> Vec3f;

struct Orientation {
    Vec3f f, s, h;
};

struct AcePlayer {
    AceMap *map;
    bool mf, mb, ml, mr, jump, crouch, sneak, sprint, primary_fire, secondary_fire;
    float lastclimb;
    int airborne, wade, alive, weapon;
    Vec3f p, e, v, f, s, h;
};

inline void get_orientation(Orientation * o, float x, float y, float z) {
    o->f.set(x, y, z);
    float f = sqrtf(x*x + y*y);
    o->s.x = -y / f;
    o->s.y = x / f;
    o->s.z = 0.0f;
    o->h.x = -z*o->s.y;
    o->h.y = z*o->s.x;
    o->h.z = x*o->s.y - y*o->s.x;
}


inline void set_orientation_vectors(float x, float y, float z, Vec3f * s, Vec3f * h)
{
    float f = sqrtf(x*x + y*y);
    s->x = -y / f;
    s->y = x / f;
    h->x = -z*s->y;
    h->y = z*s->x;
    h->z = x*s->y - y*s->x;
}

void reorient_player(AcePlayer *p, float x, float y, float z)
{
    p->f.set(x, y, z);
    set_orientation_vectors(x, y, z, &p->s, &p->h);
}


//same as isvoxelsolid but water is empty && out of bounds returns true
int clipbox(AceMap *map, float x, float y, float z)
{
    int sz;

    if (x < 0 || x >= MAP_X || y < 0 || y >= MAP_Y)
        return 1;
    else if (z < 0)
        return 0;
    sz = (int)z;
    if (sz == MAP_Z - 1)
        sz -= 1;
    else if (sz >= MAP_Z)
        return 1;
    return map->get_solid((int)x, (int)y, sz);
}

void reposition_player(AcePlayer *p, Vec3f *position, double dt, double time)
{
    float f; /* FIXME meaningful name */

    p->e = p->p = *position;
    f = p->lastclimb - time; /* FIXME meaningful name */
    if (f>-0.25f)
        p->e.z += (f + 0.25f) / 0.25f;
}


// player movement with autoclimb
void boxclipmove(AcePlayer *p, double dt, double time)
{
    float offset, m, f, nx, ny, nz, z;
    long climb = 0;

    f = dt*32.f;
    nx = f*p->v.x + p->p.x;
    ny = f*p->v.y + p->p.y;

    if (p->crouch)
    {
        offset = 0.45f;
        m = 0.9f;
    }
    else
    {
        offset = 0.9f;
        m = 1.35f;
    }

    nz = p->p.z + offset;

    if (p->v.x < 0) f = -0.45f;
    else f = 0.45f;
    z = m;
    while (z >= -1.36f && !clipbox(p->map, nx + f, p->p.y - 0.45f, nz + z) && !clipbox(p->map, nx + f, p->p.y + 0.45f, nz + z))
        z -= 0.9f;
    if (z<-1.36f) p->p.x = nx;
    else if (!p->crouch && p->f.z<0.5f && !p->sprint)
    {
        z = 0.35f;
        while (z >= -2.36f && !clipbox(p->map, nx + f, p->p.y - 0.45f, nz + z) && !clipbox(p->map, nx + f, p->p.y + 0.45f, nz + z))
            z -= 0.9f;
        if (z<-2.36f)
        {
            p->p.x = nx;
            climb = 1;
        }
        else p->v.x = 0;
    }
    else p->v.x = 0;

    if (p->v.y < 0) f = -0.45f;
    else f = 0.45f;
    z = m;
    while (z >= -1.36f && !clipbox(p->map, p->p.x - 0.45f, ny + f, nz + z) && !clipbox(p->map, p->p.x + 0.45f, ny + f, nz + z))
        z -= 0.9f;
    if (z<-1.36f) p->p.y = ny;
    else if (!p->crouch && p->f.z<0.5f && !p->sprint && !climb)
    {
        z = 0.35f;
        while (z >= -2.36f && !clipbox(p->map, p->p.x - 0.45f, ny + f, nz + z) && !clipbox(p->map, p->p.x + 0.45f, ny + f, nz + z))
            z -= 0.9f;
        if (z<-2.36f)
        {
            p->p.y = ny;
            climb = 1;
        }
        else p->v.y = 0;
    }
    else if (!climb)
        p->v.y = 0;

    if (climb)
    {
        p->v.x *= 0.5f;
        p->v.y *= 0.5f;
        p->lastclimb = time;
        nz--;
        m = -1.35f;
    }
    else
    {
        if (p->v.z < 0)
            m = -m;
        nz += p->v.z*dt*32.f;
    }

    p->airborne = 1;

    if (clipbox(p->map, p->p.x - 0.45f, p->p.y - 0.45f, nz + m) ||
        clipbox(p->map, p->p.x - 0.45f, p->p.y + 0.45f, nz + m) ||
        clipbox(p->map, p->p.x + 0.45f, p->p.y - 0.45f, nz + m) ||
        clipbox(p->map, p->p.x + 0.45f, p->p.y + 0.45f, nz + m))
    {
        if (p->v.z >= 0)
        {
            p->wade = p->p.z > 61;
            p->airborne = 0;
        }
        p->v.z = 0;
    }
    else
        p->p.z = nz - offset;

    reposition_player(p, &p->p, dt, time);
}


long move_player(AcePlayer *p, double dt, double time) {

    //move player and perform simple physics (gravity, momentum, friction)
    if (p->jump)
    {
        p->jump = false;
        p->v.z = -0.36f;
    }

    float f = dt; //player acceleration scalar
    if (p->airborne)
        f *= 0.1f;
    else if (p->crouch)
        f *= 0.3f;
    else if ((p->secondary_fire && p->weapon) || p->sneak)
        f *= 0.5f;
    else if (p->sprint)
        f *= 1.3f;

    if ((p->mf || p->mb) && (p->ml || p->mr))
        f *= sqrt(0.5); //if strafe + forward/backwards then limit diagonal velocity

    if (p->mf)
    {
        p->v.x += p->f.x*f;
        p->v.y += p->f.y*f;
    }
    else if (p->mb)
    {
        p->v.x -= p->f.x*f;
        p->v.y -= p->f.y*f;
    }
    if (p->ml)
    {
        p->v.x -= p->s.x*f;
        p->v.y -= p->s.y*f;
    }
    else if (p->mr)
    {
        p->v.x += p->s.x*f;
        p->v.y += p->s.y*f;
    }

    f = dt + 1;
    p->v.z += dt;
    p->v.z /= f; //air friction
    if (p->wade)
        f = dt*6.f + 1; //water friction
    else if (!p->airborne)
        f = dt*4.f + 1; //ground friction
    p->v.x /= f;
    p->v.y /= f;
    float f2 = p->v.z;
    boxclipmove(p, dt, time);
    //hit ground... check if hurt
    if (!p->v.z && (f2 > FALL_SLOW_DOWN))
    {
        //slow down on landing
        p->v.x *= 0.5f;
        p->v.y *= 0.5f;

        //return fall damage
        if (f2 > FALL_DAMAGE_VELOCITY)
        {
            f2 -= FALL_DAMAGE_VELOCITY;
            return f2 * f2 * FALL_DAMAGE_SCALAR;
        }

        return(-1); // no fall damage but play fall sound
    }

    return(0); //no fall damage
}