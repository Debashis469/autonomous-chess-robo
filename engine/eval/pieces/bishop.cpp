#include "bishop.hpp"
#include "../utils/bitboard.hpp"
#include "../utils/constants.hpp"

int evalBishop(uint64_t bishops, bool) {
    int score = 0;

    int count = popcount(bishops);

    score += count * BISHOP_VALUE;

    if (count >= 2)
        score += BISHOP_PAIR_BONUS;

    return score;
}