#ifndef MOVEGEN_HPP
#define MOVEGEN_HPP

#include <vector>
#include "../board/board.hpp"
#include "../move/move.hpp"

std::vector<Move> generateMoves(const Board& board);

#endif