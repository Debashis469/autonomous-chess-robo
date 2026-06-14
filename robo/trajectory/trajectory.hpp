#ifndef TRAJECTORY_HPP
#define TRAJECTORY_HPP

#include <vector>

// each step = vector of joint angles
using JointState = std::vector<double>;

// trajectory = list of steps
using Trajectory = std::vector<JointState>;

// generate trajectory
Trajectory generateTrajectory(
  const JointState& start,
  const JointState& goal,
  int steps
);

#endif