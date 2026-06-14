#include "knight.hpp"
#include "../utils/bitboard.hpp"
#include "../utils/constants.hpp"

int evalKnight(uint64_t knights, bool) {
  int score = 0;

  uint64_t temp = knights;

  while (temp) {
    int sq = lsb(temp);
    pop_bit(temp);

    score += KNIGHT_VALUE;

    int rank = sq / 8;
    int file = sq % 8;

    // center bonus
    if (rank >= 2 && rank <= 5 && file >= 2 && file <= 5) score += 20;

    // edge penalty
    if (file == 0 || file == 7 || rank == 0 || rank == 7) score -= 10;
  }

  return score;
}