#ifndef SERIAL_COMM_HPP
#define SERIAL_COMM_HPP

#include <array>
#include <string>
#include <vector>

bool initializeRobotSerial();
void shutdownRobotSerial();
bool sendTrajectory(const std::vector<std::array<std::string, 5>>& traj);

#endif
