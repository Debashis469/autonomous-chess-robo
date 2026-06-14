#include "solver.hpp"

#include <cstdint>
#include <string>
#include <vector>

#include "board/board.hpp"
#include "board/fen.hpp"
#include "movegen/legal.hpp"
#include "search/search.hpp"
#include "utils/move_to_string.hpp"

namespace {

bool hasSingleKings(const Board& board) {
    return __builtin_popcountll(board.wk) == 1 && __builtin_popcountll(board.bk) == 1;
}

bool isUsableBoard(const Board& board) {
    return hasSingleKings(board);
}

std::string terminalResult(Board& board) {
    std::vector<Move> moves = generateLegalMoves(board);
    if (!moves.empty()) return "";

    uint64_t kingBB = board.whiteToMove ? board.wk : board.bk;
    if (kingBB == 0) return "invalid";

    int kingSq = __builtin_ctzll(kingBB);
    return isSquareAttacked(board, kingSq, !board.whiteToMove) ? "checkmate" : "stalemate";
}

} // namespace

std::string solveFen(const std::string& fen, int depth) {
    Board board;
    if (!parseFEN(fen, board) || !isUsableBoard(board)) {
        return "invalid";
    }

    std::string terminal = terminalResult(board);
    if (!terminal.empty()) return terminal;

    Move bestMove = findBestMove(board, depth);
    std::string bestMoveText = moveToString(bestMove);
    return bestMoveText == "invalid" ? "invalid" : bestMoveText;
}
