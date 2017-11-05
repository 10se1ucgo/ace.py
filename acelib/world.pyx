cdef class World:
    def __init__(self, VXLMap map):
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
    def __init__(self, VXLMap map, *arg, **kwargs):
        self.map = map

    cdef long update(self, double dt, double time):
        return 0


cdef class Player:
    def __cinit__(self, VXLMap map, *arg, **kwargs):
        self.ply = new AcePlayer(map.map_data)
        self.position = math3d.new_proxy_vector(&self.ply.p)
        self.velocity = math3d.new_proxy_vector(&self.ply.v)
        self.orientation = math3d.new_proxy_vector(&self.ply.f)

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

    def set_animation(self, jump, crouch, sneak, sprint):
        self.ply.jump = jump
        self.set_crouch(crouch)
        self.ply.sneak = sneak
        self.ply.sprint = sprint

    def set_weapon(self, is_primary):
        self.ply.weapon = is_primary

    def set_walk(self, up, down, left, right):
        self.ply.mf = up
        self.ply.mb = down
        self.ply.ml = left
        self.ply.mr = right

    def set_position(self, x, y, z, reset = False):
        # self.position.set(x, y, z)
        # print(self.ply.p.x)
        self.ply.p.x = self.ply.e.x = x
        self.ply.p.y = self.ply.e.y = y
        self.ply.p.z = self.ply.e.z = z
        if reset:
            self.ply.v.x = 0
            self.ply.v.y = 0
            self.ply.v.z = 0
        # if reset:
        #     self.velocity.set(0.0, 0.0, 0.0)
        #     self.primary_fire = self.secondary_fire = False
        #     self.jump = self.crouch = False
        #     self.up = self.down = self.left = self.right = False

    def set_orientation(self, x: float, y: float, z: float):
        reorient_player(self.ply, x, y, z)

    def update(self, double dt, double time):
        return move_player(self.ply, dt, time)



