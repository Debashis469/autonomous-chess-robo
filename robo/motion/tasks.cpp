#include "tasks.hpp"

#include "primitives.hpp"
#include "../control/serial_comm.hpp"

#include <array>
#include <string>
#include <vector>

using namespace std;

const double HOVER = 12.0;

bool pick(double x, double y, double z) {
    vector<array<string, 5>> traj;

    double h = z + HOVER;
    string g = "o";

    if (!addPoint(traj, x, y, h, g)) return false;
    if (!addLinearXYZ(traj, x, y, h, x, y, z, 1, g)) return false;

    g = "c";
    if (!addPoint(traj, x, y, z, g)) return false;
    if (!addLinearXYZ(traj, x, y, z, x, y, h, 1, g)) return false;

    return sendTrajectory(traj);
}

bool place(double x, double y, double z) {
    vector<array<string, 5>> traj;

    double h = z + HOVER;
    string g = "c";

    if (!addPoint(traj, x, y, h, g)) return false;
    if (!addLinearXYZ(traj, x, y, h, x, y, z, 1, g)) return false;

    g = "o";
    if (!addPoint(traj, x, y, z, g)) return false;
    if (!addLinearXYZ(traj, x, y, z, x, y, h, 1, g)) return false;

    return sendTrajectory(traj);
}

bool pickAndPlace(
    double sx, double sy, double sz,
    double dx, double dy, double dz
) {
    vector<array<string, 5>> traj;

    string g = "o";
    double hs = sz + HOVER;

    if (!addPoint(traj, sx, sy, hs, g)) return false;
    if (!addLinearXYZ(traj, sx, sy, hs, sx, sy, sz, 10, g)) return false;

    g = "c";
    if (!addPoint(traj, sx, sy, sz, g)) return false;
    if (!addLinearXYZ(traj, sx, sy, sz, sx, sy, hs, 10, g)) return false;

    double hd = dz + HOVER;

    if (!addPoint(traj, dx, dy, hd, g)) return false;
    if (!addLinearXYZ(traj, dx, dy, hd, dx, dy, dz, 10, g)) return false;

    g = "o";
    if (!addPoint(traj, dx, dy, dz, g)) return false;
    if (!addLinearXYZ(traj, dx, dy, dz, dx, dy, hd, 10, g)) return false;

    return sendTrajectory(traj);
}

bool pickAndThrow(
    double sx, double sy, double sz,
    double tx, double ty, double tz
) {
    vector<array<string, 5>> traj;

    string g = "o";
    double hs = sz + HOVER;

    if (!addPoint(traj, sx, sy, hs, g)) return false;
    if (!addLinearXYZ(traj, sx, sy, hs, sx, sy, sz, 1, g)) return false;

    g = "c";
    if (!addPoint(traj, sx, sy, sz, g)) return false;
    if (!addLinearXYZ(traj, sx, sy, sz, sx, sy, hs, 10, g)) return false;

    double ht = tz + HOVER;

    if (!addPoint(traj, tx, ty, ht, g)) return false;
    if (!addLinearXYZ(traj, tx, ty, ht, tx, ty, tz, 10, g)) return false;

    g = "o";
    if (!addPoint(traj, tx, ty, tz, g)) return false;
    if (!addLinearXYZ(traj, tx, ty, tz, tx, ty, ht, 10, g)) return false;

    return sendTrajectory(traj);
}

bool moveRest(double x, double y, double z) {
    vector<array<string, 5>> traj;

    string g = "c";
    if (!addPoint(traj, x, y, z, g)) return false;

    return sendTrajectory(traj);
}
