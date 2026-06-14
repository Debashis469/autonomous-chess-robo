#ifndef ROBOT_PARAMS_HPP
#define ROBOT_PARAMS_HPP

#include <cmath>

// ================= LINK LENGTHS (in cm) =================
constexpr double L1 = 10.5  ;
constexpr double L2 = 29.5 ;
constexpr double L3 = 32 ;
constexpr double L4 = 19 ;

// Wrist length (L4)
constexpr double WL = L4;


// ================= ANGLE CONVERSIONS =================
// Math functions (sin, cos, atan2) use radians

constexpr double PI = 3.141592653589793;

// Degree → Radian
inline double deg2rad(double deg) {
    return deg * PI / 180.0;
}

// Radian → Degree
inline double rad2deg(double rad) {
    return rad * 180.0 / PI;
}


// ================= UTILITIES =================

// Clamp value (useful for servo limits)
inline double clamp(double val, double min_val, double max_val) {
    return (val < min_val) ? min_val : (val > max_val) ? max_val : val;
}

#endif