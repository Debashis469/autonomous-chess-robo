#include "trajectory.hpp"

Trajectory generateTrajectory(
    const JointState& start,
    const JointState& goal,
    int steps
) {
  Trajectory path;

  int n = start.size();

  for (int i = 0; i <= steps; i++) {
      
    double alpha = (double)i / steps;
      
    JointState current(n);
      
    for (int j = 0; j < n; j++) {
      current[j] = start[j] + alpha * (goal[j] - start[j]);
    }
      
    path.push_back(current);
  }

  return path;
}