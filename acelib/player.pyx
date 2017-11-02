from .math3d cimport Vector3

cimport world


cdef class Player(world.WorldObject):
    cdef public:
        Vector3 position, orientation, velocity
        bint up, down, left, right, dead, jump, airborne, crouch, sneak, wade, sprint, primary_fire, secondary_fire

    def initialize(self, Vector3 position, Vector3 orientation,
                   fall_callback = None):
        self.name = 'Player'
        self.position = position
        self.orientation = orientation
        self.velocity = Vector3()

    def set_crouch(self, bint value):
        if value == self.player.crouch:
            return
        if value:
            self.position.z += 0.9
        else:
            self.position.z -= 0.9
        self.crouch = value

    def set_animation(self, jump, crouch, sneak, sprint):
        self.player.jump = jump
        self.set_crouch(crouch)
        self.player.sneak = sneak
        self.player.sprint = sprint

    def set_weapon(self, is_primary):
        self.player.weapon = is_primary

    def set_walk(self, up, down, left, right):
        self.player.mf = up
        self.player.mb = down
        self.player.ml = left
        self.player.mr = right

    def set_position(self, x, y, z, reset = False):
        self.position.set(x, y, z)
        self.player.p.x = self.player.e.x = x
        self.player.p.y = self.player.e.y = y
        self.player.p.z = self.player.e.z = z
        if reset:
            self.velocity.set(0.0, 0.0, 0.0)
            self.primary_fire = self.secondary_fire = False
            self.jump = self.crouch = False
            self.up = self.down = self.left = self.right = False

    def set_orientation(self, x, y, z):
        cdef Vertex3 v = Vertex3(x, y, z)
        reorient_player(self.player, v.value)

    cpdef int can_see(self, float x, float y, float z):
        cdef Vertex3 position = self.position
        return can_see(self.world.map, position.x, position.y, position.z,
            x, y, z)

    cpdef cast_ray(self, length = 32.0):
        cdef Vertex3 position = self.position
        cdef Vertex3 direction = self.orientation.copy().normal()
        cdef long x, y, z
        if cast_ray(self.world.map, position.x, position.y, position.z,
            direction.x, direction.y, direction.z, length, &x, &y, &z):
            return x, y, z
        return None

    def validate_hit(self, Character other, part, float tolerance):
        cdef Vertex3 position1 = self.position
        cdef Vertex3 orientation = self.orientation
        cdef Vertex3 position2 = other.position
        cdef float x, y, z
        x = position2.x
        y = position2.y
        z = position2.z
        if part in (TORSO, ARMS):
            z += 0.9
        elif part == HEAD:
            pass
        elif part == LEGS:
            z += 1.8
        elif part == MELEE:
            z += 0.9
        else:
            return False
        if not c_validate_hit(position1.x, position1.y, position1.z,
                              orientation.x, orientation.y, orientation.z,
                              x, y, z, tolerance):
            return False
        return True

    def set_dead(self, value):
        self.player.alive = not value
        self.player.mf = False
        self.player.mb = False
        self.player.ml = False
        self.player.mr = False
        self.player.crouch = False
        self.player.sneak = False
        self.player.primary_fire = False
        self.player.secondary_fire = False
        self.player.sprint = False

    cdef int update(self, double dt) except -1:
        cdef long ret = move_player(self.player)
        if ret > 0:
            self.fall_callback(ret)
        return 0
