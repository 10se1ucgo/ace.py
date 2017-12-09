#pragma once
#include <bitset>
#include <stdint.h>
#include <vector>
#include <unordered_set>
#include <random>

struct Pos3 {
    int x, y, z;
};

constexpr size_t MAP_X = 512;
constexpr size_t MAP_Y = 512;
constexpr size_t MAP_Z = 64;
constexpr uint32_t DEFAULT_COLOR = 0xFF674028;

constexpr size_t get_pos(const int x, const int y, const int z) {
    return x + (y * MAP_Y) + (z * MAP_X * MAP_Y);
}

constexpr bool is_valid_pos(const int x, const int y, const int z) {
    return x >= 0 && x < MAP_X && y >= 0 && y < MAP_Y && z >= 0 && z < MAP_Z;
}

constexpr bool is_valid_pos(const int pos) {
    return pos >= get_pos(0, 0, 0) && pos <= get_pos(MAP_X - 1, MAP_Y - 1, MAP_Z - 1);
}


class AceMap {
public:
    AceMap(uint8_t *buf = nullptr);
    void read(uint8_t *buf);
    std::vector<uint8_t> write();
    size_t write(std::vector<uint8_t> &v, int *sx, int *sy, int columns=-1);

    bool is_surface(const int x, const int y, const int z);
    bool get_solid(int x, int y, int z, bool wrapped=false);
    uint32_t get_color(int x, int y, int z, bool wrapped=false);
    int get_z(const int x, const int y, const int start=0);
    void get_random_point(int *x, int *y, int *z, int x1, int y1, int x2, int y2);
    std::vector<Pos3> get_neighbors(int x, int y, int z);
    std::vector<Pos3> block_line(int x1, int y1, int z1, int x2, int y2, int z2) const;

    bool set_point(const int x, const int y, const int z, const bool solid, const uint32_t color);
    bool set_point(const size_t pos, const bool solid, const uint32_t color);
//    void set_column_solid(const size_t x, const size_t y, const size_t z_start, const size_t z_end, const bool solid);
//    void set_column_color(const size_t x, const size_t y, const size_t z_start, const size_t z_end, const uint32_t color);
    bool check_node(int x, int y, int z, bool destroy=true);

private:
    std::bitset<MAP_X * MAP_Y * MAP_Z> geometry;
    uint32_t colors[MAP_X * MAP_Y * MAP_Z];

    std::vector<Pos3> nodes;
    std::unordered_set<size_t> marked;

    std::default_random_engine eng;

    void add_node(std::vector<Pos3> &v, const int x, const int y, const int z) {
        if (!this->get_solid(x, y, z))
            return;
        v.push_back({ x, y, z });
    }

    void add_neighbors(std::vector<Pos3> &v, const int x, const int y, const int z) {
        this->add_node(v, x, y, z - 1);
        this->add_node(v, x, y - 1, z);
        this->add_node(v, x, y + 1, z);
        this->add_node(v, x - 1, y, z);
        this->add_node(v, x + 1, y, z);
        this->add_node(v, x, y, z + 1);
    }
};

// int check_node(int x, int y, int z, AceMap * map, int destroy);