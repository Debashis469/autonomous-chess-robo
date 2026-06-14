#include "robot_interface.hpp"

#include <iostream>

#include "../robo/control/serial_comm.hpp"
#include "../robo/robocontrol/robo_control.hpp"

using namespace std;

static const double REST_X = 0 ;
static const double REST_Y = 14;
static const double REST_Z = 12;

bool robotMove(const string& move) {
    cout << "\n[ROBOT] Move: " << move << "\n";
    return runPickPlaceMode(move);
}

bool robotCapture(const string& square) {
    cout << "\n[ROBOT] Capture at: " << square << "\n";
    return runPickThrowMode(square);
}

bool robotRest() {
    cout << "\n[ROBOT] Rest Position\n";
    return runMoveMode(REST_X, REST_Y, REST_Z);
}

void robotShutdown() {
    shutdownRobotSerial();
}
