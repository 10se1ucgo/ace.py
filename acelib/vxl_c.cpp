#include <random>
#include <chrono> 
#include <unordered_set>

#include "vxl_c.h"


template<typename T>
void write_bytes(std::vector<uint8_t> &vec, T item) {
//    char *val = reinterpret_cast<char *>(&item);
    vec.push_back(static_cast<uint8_t>(item >>  0));
    vec.push_back(static_cast<uint8_t>(item >>  8));
    vec.push_back(static_cast<uint8_t>(item >> 16));
    vec.push_back(static_cast<uint8_t>(item >> 24));
}

AceMap::AceMap(uint8_t *buf) : eng(std::chrono::system_clock::now().time_since_epoch().count()) {
    nodes.reserve(512);
    this->read(buf);
}

void AceMap::read(uint8_t *buf) {
    if (!buf) return;

    for (int y = 0; y < MAP_Y; ++y) {
        for (int x = 0; x < MAP_X; ++x) {
            int z;
            for (z = 0; z < MAP_Z; ++z) {
                this->geometry[get_pos(x, y, z)] = true;
                this->colors[get_pos(x, y, z)] = DEFAULT_COLOR;
            }


            z = 0;
            while (true) {
                int number_4byte_chunks = buf[0];
                int top_color_start = buf[1];
                int top_color_end = buf[2]; // inclusive

                for (int i = z; i < top_color_start; i++)
                    this->geometry[get_pos(x, y, i)] = false;

                uint32_t *color = reinterpret_cast<uint32_t *>(&buf[4]);
                for (z = top_color_start; z <= top_color_end; z++)
                    this->colors[get_pos(x, y, z)] = *(color++);

                int len_bottom = top_color_end - top_color_start + 1;

                // check for end of data marker
                if (number_4byte_chunks == 0) {
                    // infer ACTUAL number of 4-byte chunks from the length of the color data
                    buf += 4 * (len_bottom + 1);
                    break;
                }

                // infer the number of bottom colors in next span from chunk length
                int len_top = (number_4byte_chunks - 1) - len_bottom;

                // now skip the v pointer past the data to the beginning of the next span
                buf += buf[0] * 4;

                int bottom_color_end = buf[3]; // aka air start
                int bottom_color_start = bottom_color_end - len_top;

                for (z = bottom_color_start; z < bottom_color_end; ++z) {
                    this->colors[get_pos(x, y, z)] = *color++;
                }
            }
        }
    }
}

std::vector<uint8_t> AceMap::write() {
    std::vector<uint8_t> v;
    v.reserve(5 * 1024 * 1024);
    int x = 0, y = 0;
    this->write(v, &x, &y);
    return v;
}

size_t AceMap::write(std::vector<uint8_t> &v, int *sx, int *sy, int columns) {
    size_t initial_size = v.size();
    int column = 0;
    const bool all = columns < 0;

    int y, x;
    for (y = *sy; y < MAP_Y; ++y) {
        for (x = *sx; x < MAP_X; ++x) {
            if (!all && column >= columns) {
                goto done;
            }
            int z = 0;
            while (z < MAP_Z) {
                // find the air region
                int air_start = z;
                while (z < MAP_Z && !this->geometry[get_pos(x, y, z)])
                    ++z;

                // find the top region
                int top_colors_start = z;
                while (z < MAP_Z && this->is_surface(x, y, z))
                    ++z;
                int top_colors_end = z;

                // now skip past the solid voxels
                while (z < MAP_Z && this->geometry[get_pos(x, y, z)] && !this->is_surface(x, y, z))
                    ++z;

                // at the end of the solid voxels, we have colored voxels.
                // in the "normal" case they're bottom colors; but it's
                // possible to have air-color-solid-color-solid-color-air,
                // which we encode as air-color-solid-0, 0-color-solid-air

                // so figure out if we have any bottom colors at this point
                int bottom_colors_start = z;

                int i = z;
                while (i < MAP_Z && this->is_surface(x, y, i))
                    ++i;

                if (i != MAP_Z) {
                    // these are real bottom colors so we can write them
                    while (is_surface(x, y, z))
                        ++z;
                }
                int bottom_colors_end = z;

                // now we're ready to write a span
                int top_colors_len = top_colors_end - top_colors_start;
                int bottom_colors_len = bottom_colors_end - bottom_colors_start;

                int colors = top_colors_len + bottom_colors_len;

                if (z == MAP_Z)
                    v.push_back(0);
                else
                    v.push_back(colors + 1);

                v.push_back(top_colors_start);
                v.push_back(top_colors_end - 1);
                v.push_back(air_start);

                for (i = 0; i < top_colors_len; ++i)
                    write_bytes(v, this->colors[get_pos(x, y, top_colors_start + i)]);
                    
                for (i = 0; i < bottom_colors_len; ++i)
                    write_bytes(v, this->colors[get_pos(x, y, bottom_colors_start + i)]);
            }
            column++;
        }
        *sx = 0;
    }
done:
    *sx = x;
    *sy = y;
    return v.size() - initial_size;
}

bool AceMap::is_surface(const int x, const int y, const int z) {
    if (!this->geometry[get_pos(x, y, z)]) return false;
    if (x     >     0 && !this->geometry[get_pos(x - 1, y, z)]) return true;
    if (x + 1 < MAP_X && !this->geometry[get_pos(x + 1, y, z)]) return true;
    if (y     >     0 && !this->geometry[get_pos(x, y - 1, z)]) return true;
    if (y + 1 < MAP_Y && !this->geometry[get_pos(x, y + 1, z)]) return true;
    if (z     >     0 && !this->geometry[get_pos(x, y, z - 1)]) return true;
    if (z + 1 < MAP_Z && !this->geometry[get_pos(x, y, z + 1)]) return true;
    return false;
}

bool AceMap::get_solid(int x, int y, int z, bool wrapped) {
    if (wrapped) {
        x &= (MAP_X - 1);
        y &= (MAP_Y - 1);
    }
    if (!is_valid_pos(x, y, z))
        return false;
    return this->geometry[get_pos(x, y, z)];
}

uint32_t AceMap::get_color(int x, int y, int z, bool wrapped) {
    if (wrapped) {
        x &= (MAP_X - 1);
        y &= (MAP_Y - 1);
    }
    if (!is_valid_pos(x, y, z)) return 0;
    return this->colors[get_pos(x, y, z)];
}

int AceMap::get_z(const int x, const int y, const int start) {
    for(int z = start; z < MAP_Z; z++) {
        if (this->get_solid(x, y, z)) return z;
    }
    return MAP_Z;
}

void AceMap::get_random_point(int *x, int *y, int *z, int x1, int y1, int x2, int y2) {
    std::uniform_int_distribution<int> xdist(x1, x2 - 1);
    std::uniform_int_distribution<int> ydist(y1, y2 - 1);

    int rx = 0, ry = 0, rz = 0;
    for(int i = 0; i < 16; i++) {
        rx = xdist(this->eng); ry = ydist(this->eng); rz = this->get_z(rx, ry);
        if(rz < MAP_Z - 2 && this->get_solid(rx, ry, rz)) {
            break;
        }
    }
    *x = rx; *y = ry; *z = rz;
}

std::vector<Pos3> AceMap::get_neighbors(int x, int y, int z) {
    std::vector<Pos3> neighbors;
    this->add_neighbors(neighbors, x, y, z);
    return neighbors;
}

std::vector<Pos3> AceMap::block_line(int x1, int y1, int z1, int x2, int y2, int z2) const {
    std::vector<Pos3> ret;

    Pos3 c{ x1, y1, z1 };
    Pos3 d{ x2 - x1, y2 - y1, z2 - z1 };
    long ixi, iyi, izi, dx, dy, dz, dxi, dyi, dzi;
    const size_t VSID = MAP_X;

    if (d.x < 0) ixi = -1;
    else ixi = 1;
    if (d.y < 0) iyi = -1;
    else iyi = 1;
    if (d.z < 0) izi = -1;
    else izi = 1;

    if ((abs(d.x) >= abs(d.y)) && (abs(d.x) >= abs(d.z)))
    {
        dxi = 1024; dx = 512;
        dyi = static_cast<long>(!d.y ? 0x3fffffff / VSID : abs(d.x * 1024 / d.y));
        dy = dyi / 2;
        dzi = static_cast<long>(!d.z ? 0x3fffffff / VSID : abs(d.x * 1024 / d.z));
        dz = dzi / 2;
    }
    else if (abs(d.y) >= abs(d.z))
    {
        dyi = 1024; dy = 512;
        dxi = static_cast<long>(!d.x ? 0x3fffffff / VSID : abs(d.y * 1024 / d.x));
        dx = dxi / 2;
        dzi = static_cast<long>(!d.z ? 0x3fffffff / VSID : abs(d.y * 1024 / d.z));
        dz = dzi / 2;
    }
    else
    {
        dzi = 1024; dz = 512;
        dxi = static_cast<long>(!d.x ? 0x3fffffff / VSID : abs(d.z * 1024 / d.x));
        dx = dxi / 2;
        dyi = static_cast<long>(!d.y ? 0x3fffffff / VSID : abs(d.z * 1024 / d.y));
        dy = dyi / 2;
    }
    if (ixi >= 0) dx = dxi - dx;
    if (iyi >= 0) dy = dyi - dy;
    if (izi >= 0) dz = dzi - dz;

    while (true) {
        ret.push_back(c);

        if (c.x == x2 &&
            c.y == y2 &&
            c.z == z2)
            break;

        if ((dz <= dx) && (dz <= dy))
        {
            c.z += izi;
            if (c.z < 0 || c.z >= MAP_Z)
                break;
            dz += dzi;
        }
        else
        {
            if (dx < dy)
            {
                c.x += ixi;
                if (static_cast<unsigned long>(c.x) >= VSID)
                    break;
                dx += dxi;
            }
            else
            {
                c.y += iyi;
                if (static_cast<unsigned long>(c.y) >= VSID)
                    break;
                dy += dyi;
            }
        }
    }
    return ret;
}

bool AceMap::set_point(const int x, const int y, const int z, const bool solid, const uint32_t color) {
    return this->set_point(get_pos(x, y, z), solid, color);
}

bool AceMap::set_point(const size_t pos, const bool solid, const uint32_t color) {
    if (!is_valid_pos(pos)) return false;

    this->geometry[pos] = solid;
    this->colors[pos] = solid ? color : DEFAULT_COLOR;
    return true;
}

bool AceMap::check_node(int x, int y, int z, bool destroy) {
    marked.clear();
    nodes.clear();
    nodes.push_back({x, y, z});

    while (!nodes.empty()) {
        const Pos3 &node = nodes.back();
        x = node.x; y = node.y; z = node.z;
        nodes.pop_back();
        if (z >= 62) {
            return true;
        }

        // already visited?
        auto ret = marked.insert(get_pos(x, y, z));
        if (ret.second) {
            this->add_neighbors(nodes, x, y, z);
        }
    }

    // destroy the node's path!
    if (destroy) {
        for(auto pos : marked) {
            this->set_point(pos, false, 0);
        }
    }
    return true;
}