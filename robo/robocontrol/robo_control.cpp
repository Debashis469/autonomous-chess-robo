#include "robo_control.hpp"

#include <iostream>
#include <tuple>

#include "../kinematics/ik.hpp"
#include "../motion/tasks.hpp"
#include "../utils/chess_map.hpp"

using namespace std;

bool runIKMode() {
    double x, y, z;

    cout << "Enter target position (x y z): ";
    cin >> x >> y >> z;

    IKCandidate sol = inverseKinematics(x, y, z);

    if (!sol.valid) {
        cout << "No valid IK solution found.\n";
        return false;
    }

    cout << "\nBest IK solution:\n";

    for (int i = 0; i < 4; i++) {
        cout << "theta" << i + 1 << " = "
             << sol.theta_deg[i] << "\n";
    }

    cout << "error = " << sol.error << "\n";
    return true;
}

bool runPickMode(const string& sq) {
    if (!isValidSquare(sq)) {
        cout << "Invalid square!\n";
        return false;
    }

    tuple<double, double, double> sqPos = getCoord(sq);

    double x = get<0>(sqPos);
    double y = get<1>(sqPos);
    double z = get<2>(sqPos);

    return pick(x, y, z);
}

bool runPickMode() {
    string sq;

    cout << "Enter square (e.g. e4): ";
    cin >> sq;

    return runPickMode(sq);
}

bool runPickPlaceMode(const string& move) {
    if (move.size() != 4) {
        cout << "Invalid format!\n";
        return false;
    }

    string s = move.substr(0, 2);
    string d = move.substr(2, 2);

    if (!isValidSquare(s) || !isValidSquare(d)) {
        cout << "Invalid squares!\n";
        return false;
    }

    tuple<double, double, double> sPos = getCoord(s);
    tuple<double, double, double> dPos = getCoord(d);

    double sx = get<0>(sPos);
    double sy = get<1>(sPos);
    double sz = get<2>(sPos);

    double dx = get<0>(dPos);
    double dy = get<1>(dPos);
    double dz = get<2>(dPos);

    return pickAndPlace(sx, sy, sz, dx, dy, dz);
}

bool runPickPlaceMode() {
    string move;

    cout << "Enter move (e.g. e2e4): ";
    cin >> move;

    return runPickPlaceMode(move);
}

bool runPickThrowMode(const string& sq) {
    if (!isValidSquare(sq)) {
        cout << "Invalid square!\n";
        return false;
    }

    tuple<double, double, double> sPos = getCoord(sq);

    double sx = get<0>(sPos);
    double sy = get<1>(sPos);
    double sz = get<2>(sPos);

    double tx = 25;
    double ty = 30;
    double tz = 15;

    return pickAndThrow(sx, sy, sz, tx, ty, tz);
}

bool runPickThrowMode() {
    string sq;

    cout << "Enter square (e.g. h6): ";
    cin >> sq;

    return runPickThrowMode(sq);
}

bool runMoveMode(double x, double y, double z) {
    return moveRest(x, y, z);
}

bool runMoveMode() {
    double x, y, z;

    cout << "Enter rest position (x y z): ";
    cin >> x >> y >> z;

    return runMoveMode(x, y, z);
}
