#ifndef ROBO_CONTROL_HPP
#define ROBO_CONTROL_HPP

#include <string>

bool runIKMode();

bool runPickMode();
bool runPickMode(const std::string& sq);

bool runPickPlaceMode();
bool runPickPlaceMode(const std::string& move);

bool runPickThrowMode();
bool runPickThrowMode(const std::string& sq);

bool runMoveMode();
bool runMoveMode(double x, double y, double z);

#endif
