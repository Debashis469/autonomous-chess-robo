#ifndef IK_HPP
#define IK_HPP

#include <array>
#include <vector>

struct IKCandidate {
  bool valid = false;
  std::array<double, 4> theta_deg{};  // [θ1, θ2, θ3, θ4] in degrees
  double error = 1e18;                // smaller is better
  int branch_id = -1;                 // optional debug: 0..3
};

// Returns all valid candidate solutions
std::vector<IKCandidate> inverseKinematicsAll(double wx, double wy, double wz);

// Returns the best valid solution after filtering and error comparison
IKCandidate inverseKinematics(double wx, double wy, double wz);

#endif