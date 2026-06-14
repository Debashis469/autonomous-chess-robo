#include "pawn.hpp"
#include "../utils/bitboard.hpp"
#include "../utils/constants.hpp"

int evalPawn(uint64_t pawns, uint64_t enemyPawns, bool isWhite) {
    int score = 0;

    // FILE MASK (vertical column)
    const uint64_t FILE_A = 0x0101010101010101ULL;

    // -------- 1. DOUBLED PAWNS (once per file) --------
    for (int file = 0; file < 8; file++) {
      uint64_t fileMask = FILE_A << file;
      int count = popcount(pawns & fileMask);

      if (count > 1) score += DOUBLED_PAWN_PENALTY * (count - 1);
    }

    // -------- 2. LOOP EACH PAWN --------
    uint64_t temp = pawns;

    while (temp) {
      int sq = lsb(temp);
      pop_bit(temp);

      score += PAWN_VALUE;

      int file = sq % 8;
      int rank = sq / 8;

      // -------- 3. ISOLATED PAWN --------
      bool isolated = true;

      if (file > 0) {
          uint64_t leftFile = FILE_A << (file - 1);
          if (pawns & leftFile) isolated = false;
      }

        if (file < 7) {
            uint64_t rightFile = FILE_A << (file + 1);
            if (pawns & rightFile) isolated = false;
        }

        if (isolated)
            score += ISOLATED_PAWN_PENALTY;

        // -------- 4. PASSED PAWN --------
        uint64_t passedMask = 0ULL;

        for (int f = file - 1; f <= file + 1; f++) {
            if (f < 0 || f > 7) continue;

            uint64_t fileMask = FILE_A << f;

            if (isWhite) {
                // squares ahead
                uint64_t forward = fileMask & (~((1ULL << (sq + 1)) - 1));
                passedMask |= forward;
            } else {
                // squares behind (from black POV)
                uint64_t backward = fileMask & ((1ULL << sq) - 1);
                passedMask |= backward;
            }
        }

        if ((enemyPawns & passedMask) == 0) score += PASSED_PAWN_BONUS;

        // -------- 5. ADVANCEMENT BONUS --------
        if (isWhite) score += rank * 5;
        else score += (7 - rank) * 5;
    }

    return score;
}