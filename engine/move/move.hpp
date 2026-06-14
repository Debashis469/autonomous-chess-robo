#ifndef MOVE_HPP
#define MOVE_HPP

#include "../utils/types.hpp"

struct Move {
  int from, to;
  int piece;
  int captured;
  int promotion;
  int flag;

  Move(int f, int t, int p, int cap = -1, int promo = -1, int fl = QUIET)
    : from(f), to(t), piece(p), captured(cap), promotion(promo), flag(fl) {}
};

#endif