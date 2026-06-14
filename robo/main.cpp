#include <iostream>

#include "control/serial_comm.hpp"
#include "robocontrol/robo_control.hpp"

using namespace std;

int main() {
    int mode;
    bool ok = false;

    cout << "\n===== ROBOT CONTROL MENU =====\n";
    cout << "1. IK Test Mode\n";
    cout << "2. Pick (chess square)\n";
    cout << "3. Pick and Place (e2e4)\n";
    cout << "4. Pick and Throw\n";
    cout << "5. Move To Rest Position\n";
    cout << "Select mode: ";

    cin >> mode;

    switch (mode) {
        case 1:
            ok = runIKMode();
            break;

        case 2:
            ok = runPickMode();
            break;

        case 3:
            ok = runPickPlaceMode();
            break;

        case 4:
            ok = runPickThrowMode();
            break;

        case 5:
            ok = runMoveMode();
            break;

        default:
            cout << "Invalid mode selected.\n";
            ok = false;
            break;
    }

    if (!ok) {
        cout << "Operation failed.\n";
    }

    shutdownRobotSerial();
    return ok ? 0 : 1;
}
