#pragma once
#include <string>
#include <tuple>

bool isValidSquare(const std::string& sq);

// returns (x, y, z)
std::tuple<double, double, double> getCoord(const std::string& sq);