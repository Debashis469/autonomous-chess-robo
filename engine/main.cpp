#include <iostream>
#include <string>

#include "solver.hpp"

int main() {
    std::string fen;
    std::getline(std::cin, fen);

    std::cout << solveFen(fen, 4) << "\n";
    return 0;
}
