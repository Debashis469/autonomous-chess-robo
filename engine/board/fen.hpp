#ifndef FEN_HPP
#define FEN_HPP

#include <string>
#include "board.hpp"

bool parseFEN(const std::string& fen, Board& board);

#endif
