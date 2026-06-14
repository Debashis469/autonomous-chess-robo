#include "ik.hpp"
#include "../config/robo_params.hpp"

#include <cmath>
#include <limits>

namespace {

// Numerical tolerance
constexpr double EPS = 1e-9;

// Clamp to [-1, 1] for safe acos/sqrt domain handling
double clampToUnit(double x) {
  if (x > 1.0) return 1.0;
  if (x < -1.0) return -1.0;
  return x;
}

double radToDeg(double r) {
  return rad2deg(r);
}

double degToRad(double d) {
  return deg2rad(d);
}

} // namespace

std::vector<IKCandidate> inverseKinematicsAll(double wx, double wy, double wz) {
  std::vector<IKCandidate> solutions;

  // Base rotation
  const double theta1_rad = std::atan2(wy, wx);

  // Planar reduction
  const double delta = std::sqrt(wx * wx + wy * wy) ;
  const double gamma = wz - L1;

  const double R2 = delta * delta + gamma * gamma;
  if (R2 < EPS) {
    return solutions; // degenerate target
  }

  // Cosine law for theta3
  const double c3_raw = (R2 - L2 * L2 - L3 * L3) / (2.0 * L2 * L3);

  // No real solution if outside reachable range
  if (c3_raw < -1.0 - 1e-7 || c3_raw > 1.0 + 1e-7) {
    return solutions;
  }

  const double c3 = clampToUnit(c3_raw);
  const double s3_abs = std::sqrt(std::max(0.0, 1.0 - c3 * c3));

  // Two elbow branches: s3 = + and -
  for (int s3_sign_idx = 0; s3_sign_idx < 2; ++s3_sign_idx) {
    const double s3 = (s3_sign_idx == 0) ? s3_abs : -s3_abs;
    const double theta3_rad = std::atan2(s3, c3);

    // Your formula for s2
    const double s2_raw = ((L2 + L3 * c3) * gamma - (L3 * s3) * delta) / R2;

    if (s2_raw < -1.0 - 1e-7 || s2_raw > 1.0 + 1e-7) {
      continue;
    }

    const double s2 = clampToUnit(s2_raw);
    const double c2_abs = std::sqrt(std::max(0.0, 1.0 - s2 * s2));

    // Two shoulder branches: c2 = + and -
    for (int c2_sign_idx = 0; c2_sign_idx < 2; ++c2_sign_idx) {
      const double c2 = (c2_sign_idx == 0) ? c2_abs : -c2_abs;
      const double theta2_rad = std::atan2(s2, c2);

      // Discard negative theta2 as you requested
      if (theta2_rad < -EPS || theta3_rad > EPS) {
        continue;
      }

      // Forward-check the candidate using the same 2-link geometry
      const double delta_hat = L2 * std::cos(theta2_rad) + L3 * std::cos(theta2_rad + theta3_rad);
      const double gamma_hat = L2 * std::sin(theta2_rad) + L3 * std::sin(theta2_rad + theta3_rad);
      const double err = std::hypot(delta_hat - delta, gamma_hat - gamma);

      // Wrist angles from your convention
      const double theta4_rad = -(degToRad(90.0) + theta2_rad + theta3_rad);

      IKCandidate cand;
      cand.valid = true;
      cand.error = err;
      cand.branch_id = s3_sign_idx * 2 + c2_sign_idx;

      cand.theta_deg[0] = radToDeg(theta1_rad);
      cand.theta_deg[1] = radToDeg(theta2_rad);
      cand.theta_deg[2] = radToDeg(theta3_rad);
      cand.theta_deg[3] = radToDeg(theta4_rad);

      solutions.push_back(cand);
    }
  }

  return solutions;
}

IKCandidate inverseKinematics(double x, double y, double z) {
  double wx = x;
  double wy = y;
  double wz = z+WL;
  const std::vector<IKCandidate> all = inverseKinematicsAll(wx, wy, wz);

  IKCandidate best;
  best.valid = false;
  best.error = std::numeric_limits<double>::infinity();
  for (const auto& cand : all) {
    if (!cand.valid) continue ;
    if (cand.error < best.error) {
      best = cand ;
    }
  }

  return best;
}