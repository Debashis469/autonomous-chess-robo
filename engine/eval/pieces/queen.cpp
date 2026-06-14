#include "queen.hpp"
#include "../utils/bitboard.hpp"
#include "../utils/constants.hpp"

int evalQueen(uint64_t queens, bool) {
    return popcount(queens) * QUEEN_VALUE;
}