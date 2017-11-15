cdef extern from "math.h":
    double floor(double x)

def cast_ray(vxl.VXLMap map, math3d.Vector3 pos, math3d.Vector3 dir, double length=32, bint isdirection=True):
    cdef long x, y, z
    if c_cast_ray(map.map_data, pos.c_vec[0], dir.c_vec[0], &x, &y, &z, length, isdirection):
        return x, y, z
    else:
        return False


cdef class World:
    def __init__(self, vxl.VXLMap map):
        self.map = map
        self.objects = []

    def update(self, double dt, double time):
        if self.map is None:
            return
        # set_globals(self.map.map, self.time, dt)
        cdef WorldObject instance
        for instance in self.objects:
            instance.update(dt, time)
    #
    # cpdef delete_object(self, WorldObject item):
    #     self.objects.remove(item)
    #
    def create_object(self, klass, *arg, **kw):
        new_object = klass(self, *arg, **kw)
        self.objects.append(new_object)
        return new_object

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
    def dead(self):
        return not self.ply.alive

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


# A generic object with collision detection
cdef class GenericMovement:
    def __init__(self, vxl.VXLMap map, double x, double y, double z):
        self.map = map
        self.position = math3d.Vector3(x, y, z)

    def update(self, double dt, double time):
        return clipbox(self.map.map_data, floor(self.position.x), floor(self.position.y), floor(self.position.z))
