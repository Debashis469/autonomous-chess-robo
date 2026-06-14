#ifndef PRIMITIVES_HPP
#define PRIMITIVES_HPP

#include <array>
#include <string>
#include <vector>

bool addPoint(
    std::vector<std::array<std::string, 5>>& traj,
    double x, double y, double z,
    const std::string& grip
);

bool addLinearXYZ(
    std::vector<std::array<std::string, 5>>& traj,
    double x1, double y1, double z1,
    double x2, double y2, double z2,
    int steps,
    const std::string& grip
);

#endif
