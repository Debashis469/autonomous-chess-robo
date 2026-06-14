#ifndef BOARD_HPP
#define BOARD_HPP

#include <cstdint>

struct Board {
    // White pieces
    uint64_t wp = 0, wn = 0, wb = 0, wr = 0, wq = 0, wk = 0;

    // Black pieces
    uint64_t bp = 0, bn = 0, bb = 0, br = 0, bq = 0, bk = 0;

    // Game state
    bool whiteToMove = true;

    int castlingRights = 0; 
    // 1 = K, 2 = Q, 4 = k, 8 = q

    int enPassantSquare = -1; // -1 = none
};

#endif