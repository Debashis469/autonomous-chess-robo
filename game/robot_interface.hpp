#ifndef ROBOT_INTERFACE_HPP
#define ROBOT_INTERFACE_HPP

#include <string>

bool robotMove(const std::string& move);
bool robotCapture(const std::string& square);
bool robotRest();
void robotShutdown();

#endif
