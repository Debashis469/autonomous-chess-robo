#include "rook.hpp"
#include "../utils/bitboard.hpp"
#include "../utils/constants.hpp"

int evalRook(uint64_t rooks, uint64_t ownPawns, uint64_t enemyPawns, bool) {
  int score = 0;

  uint64_t temp = rooks;

  while (temp) {
      int sq = lsb(temp);
      pop_bit(temp);

      score += ROOK_VALUE;

      int file = sq % 8;

      uint64_t fileMask = 0x0101010101010101ULL << file;

      bool ownPawn = ownPawns & fileMask;
      bool enemyPawn = enemyPawns & fileMask;

      if (!ownPawn && !enemyPawn) score += 20;       // open
      else if (!ownPawn && enemyPawn) score += 10;   // half-open
  }

  return score;
}