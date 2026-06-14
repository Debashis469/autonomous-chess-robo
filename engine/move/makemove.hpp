#ifndef MAKEMOVE_HPP
#define MAKEMOVE_HPP

#include "../board/board.hpp"
#include "move.hpp"

struct Undo {
    bool whiteToMove;
    int castlingRights;
    int enPassantSquare;

    uint64_t wp, wn, wb, wr, wq, wk;
    uint64_t bp, bn, bb, br, bq, bk;
};

void makeMove(Board& board, const Move& move, Undo& undo);
void undoMove(Board& board, const Move& move, const Undo& undo);

#endif
