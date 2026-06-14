#include "primitives.hpp"

#include "../kinematics/ik.hpp"

#include <iomanip>
#include <iostream>
#include <sstream>

using namespace std;

static string toStr(double val) {
    stringstream ss;
    ss << fixed << setprecision(2) << val;
    return ss.str();
}

bool addPoint(
    vector<array<string, 5>>& traj,
    double x, double y, double z,
    const string& grip
) {
    IKCandidate sol = inverseKinematics(x, y, z);
    if (!sol.valid) {
        cerr << "[IK] No valid solution for target ("
             << x << ", " << y << ", " << z << ")\n";
        return false;
    }

    array<string, 5> step;

    for (int i = 0; i < 4; i++) {
        step[i] = toStr(sol.theta_deg[i]);
    }

    step[4] = grip;
    traj.push_back(step);
    return true;
}

bool addLinearXYZ(
    vector<array<string, 5>>& traj,
    double x1, double y1, double z1,
    double x2, double y2, double z2,
    int steps,
    const string& grip
) {
    if (steps <= 0) {
        return addPoint(traj, x2, y2, z2, grip);
    }

    for (int i = 1; i <= steps; i++) {
        double t = static_cast<double>(i) / steps;

        double x = x1 + t * (x2 - x1);
        double y = y1 + t * (y2 - y1);
        double z = z1 + t * (z2 - z1);

        if (!addPoint(traj, x, y, z, grip)) {
            return false;
        }
    }

    return true;
}
