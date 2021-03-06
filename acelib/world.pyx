cdef extern from "math.h":
    double floor(double x)

def cast_ray(vxl.VXLMap map, math3d.Vector3 pos, math3d.Vector3 dir, double length=32, bint isdirection=True):
    cdef long x, y, z
    if c_cast_ray(map.map_data, pos.c_vec[0], dir.c_vec[0], &x, &y, &z, length, isdirection):
        return x, y, z
    else:
        return False


cdef class WorldObject:
    def __init__(self, vxl.VXLMap map, *arg, **kwargs):
        self.map = map

    cdef long update(self, double dt, double time):
        return 0


cdef class Player:
    def __cinit__(self, vxl.VXLMap map):
        self.ply = new AcePlayer(map.map_data)
        self.position = math3d.new_proxy_vector(&self.ply.p)
        self.velocity = math3d.new_proxy_vector(&self.ply.v)
        self.orientation = math3d.new_proxy_vector(&self.ply.f)
        self.eye = math3d.new_proxy_vector(&self.ply.e)

    def __init__(self, vxl.VXLMap map):
        pass

    def __dealloc__(self):
        del self.ply

    def set_crouch(self, bint value):
        if value == self.ply.crouch:
            return
        if value:
            self.ply.p.z += 0.9
        else:
            self.ply.p.z -= 0.9
        self.ply.crouch = value

    def set_animation(self, bint jump, bint crouch, bint sneak, bint sprint):
        if self.ply.airborne:
            jump = False
        self.ply.jump = jump
        self.set_crouch(crouch)
        self.ply.sneak = sneak
        self.ply.sprint = sprint

    def set_weapon(self, bint is_primary):
        self.ply.weapon = is_primary

    def set_walk(self, bint up, bint down, bint left, bint right):
        self.ply.mf = up
        self.ply.mb = down
        self.ply.ml = left
        self.ply.mr = right

    def set_fire(self, bint primary, bint secondary):
        self.ply.primary_fire = primary
        self.ply.secondary_fire = secondary

    def set_position(self, double x, double y, double z, bint reset=False):
        self.ply.p.set(x, y, z)
        self.ply.e.set(x, y, z)
        if reset:
            self.ply.v.set(0, 0, 0)
            self.set_walk(False, False, False, False)
            self.set_animation(False, False, False, False)
            self.set_fire(False, False)
            self.set_weapon(True)

    def set_dead(self, bint dead):
        self.ply.alive = not dead

    @property
    def mf(self):
        return self.ply.mf
    @mf.setter
    def mf(self, value):
        self.ply.mf = value

    @property
    def mb(self):
        return self.ply.mb
    @mb.setter
    def mb(self, value):
        self.ply.mb = value

    @property
    def ml(self):
        return self.ply.ml
    @ml.setter
    def ml(self, value):
        self.ply.ml = value

    @property
    def mr(self):
        return self.ply.mr
    @mr.setter
    def mr(self, value):
        self.ply.mr = value

    @property
    def jump(self):
        return self.ply.jump
    @jump.setter
    def jump(self, value):
        self.ply.jump = value

    @property
    def crouch(self):
        return self.ply.crouch
    @crouch.setter
    def crouch(self, value):
        self.set_crouch(value)

    @property
    def sneak(self):
        return self.ply.sneak
    @sneak.setter
    def sneak(self, value):
        self.ply.sneak = value

    @property
    def sprint(self):
        return self.ply.sneak
    @sprint.setter
    def sprint(self, value):
        self.ply.sprint = value

    @property
    def airborne(self):
        return self.ply.airborne

    @property
    def wade(self):
        return self.ply.wade

    @property
    def dead(self):
        return not self.ply.alive
    @dead.setter
    def dead(self, bint val):
        self.ply.alive = not val

    def set_orientation(self, double x, double y, double z):
        self.ply.set_orientation(x, y, z)

    def update(self, double dt, double time):
        return self.ply.update(dt, time)


cdef class Grenade:
    def __cinit__(self, vxl.VXLMap map, double px, double py, double pz, double vx, double vy, double vz):
        self.grenade = new AceGrenade(map.map_data, px, py, pz, vx, vy, vz)
        self.position = math3d.new_proxy_vector(&self.grenade.p)
        self.velocity = math3d.new_proxy_vector(&self.grenade.v)

    def __init__(self, vxl.VXLMap map, double px, double py, double pz, double vx, double vy, double vz):
        pass

    def __dealloc__(self):
        del self.grenade

    def update(self, double dt, double time):
        return self.grenade.update(dt, time)

    def next_collision(self, double dt, double max):
        cdef:
            double eta
            math3d.Vector3 pos = math3d.new_vector3(0, 0, 0)
        collides = self.grenade.next_collision(dt, max, &eta, pos.c_vec)
        if collides:
            return eta, pos
        else:
            return False, pos


# A generic object with collision detection
cdef class GenericMovement:
    def __init__(self, vxl.VXLMap map, double x, double y, double z):
        self.map = map
        self.position = math3d.Vector3(x, y, z)

    def update(self, double dt, double time):
        return clipbox(self.map.map_data, floor(self.position.x), floor(self.position.y), floor(self.position.z))
