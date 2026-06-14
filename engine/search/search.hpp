#ifndef SEARCH_HPP
#define SEARCH_HPP

#include "../board/board.hpp"
#include "../move/move.hpp"

struct SearchResult {
    Move bestMove = Move(-1, -1, KING);
    int eval = 0;
    int depth = 0;
};

SearchResult searchBestMove(Board& board, int depth);
Move findBestMove(Board& board, int depth);

#endif
