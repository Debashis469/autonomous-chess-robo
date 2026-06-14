#ifndef LEGAL_HPP
#define LEGAL_HPP

#include <vector>
#include "../board/board.hpp"
#include "../move/move.hpp"

bool isSquareAttacked(const Board& b, int sq, bool byWhite);

std::vector<Move> generateLegalMoves(Board& b);

#endif