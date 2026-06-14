#include "move_to_string.hpp"

std::string squareToString(int sq) {
    if (sq < 0 || sq >= 64) return "??";

    char file = 'a' + (sq % 8);
    char rank = '1' + (sq / 8);
    return std::string() + file + rank;
}

std::string moveToString(const Move& m) {
    if (m.from < 0 || m.from >= 64 || m.to < 0 || m.to >= 64) return "invalid";
    return squareToString(m.from) + squareToString(m.to);
}
