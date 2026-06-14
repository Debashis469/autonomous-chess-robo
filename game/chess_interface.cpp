#include "chess_interface.hpp"

// solveFen()
#include "../engine/solver.hpp"

using namespace std;

string getEngineMove(const string& fen) {

    return solveFen(fen, 4);
}