#include <iostream>
#include "search.hpp"
#include "../movegen/legal.hpp"
#include "../move/makemove.hpp"
#include "../eval/eval.hpp"
#include <limits>

using namespace std;

const int INF = 1e9;

// ================= ALPHA-BETA =================

int alphaBeta(Board& b, int depth, int alpha, int beta) {

    if (depth == 0) {
        return evaluate( b.wp, b.wn, b.wb, b.wr, b.wq, b.wk, b.bp, b.bn, b.bb, b.br, b.bq, b.bk );
    }

    vector<Move> moves = generateLegalMoves(b);

    // ================= TERMINAL =================

    if (moves.empty()) {
        // checkmate or stalemate
        uint64_t kingBB = b.whiteToMove ? b.wk : b.bk;
        if (kingBB == 0) {
            return 0;
        }

        int kingSq = __builtin_ctzll(kingBB);

        if (isSquareAttacked(b, kingSq, !b.whiteToMove)) {
            return -INF + depth; // checkmate
        } else {
            return 0; // stalemate
        }
    }

    // ================= MAX PLAYER =================

    if (b.whiteToMove) {
        int maxEval = -INF;

        for (auto& m : moves) {
            Undo u;
            makeMove(b, m, u);

            int eval = alphaBeta(b, depth - 1, alpha, beta);

            undoMove(b, m, u);

            maxEval = max(maxEval, eval);
            alpha = max(alpha, eval);

            if (beta <= alpha) break; // PRUNE
        }

        return maxEval;
    }

    // ================= MIN PLAYER =================

    else {
        int minEval = INF;

        for (auto& m : moves) {
            Undo u;
            makeMove(b, m, u);

            int eval = alphaBeta(b, depth - 1, alpha, beta);

            undoMove(b, m, u);

            minEval = min(minEval, eval);
            beta = min(beta, eval);

            if (beta <= alpha) break; // PRUNE
        }

        return minEval;
    }
}

// ================= ROOT =================

SearchResult searchBestMove(Board& b, int depth) {
    SearchResult result;
    result.depth = depth;

    vector<Move> moves = generateLegalMoves(b);
    if (moves.empty()) {
        uint64_t kingBB = b.whiteToMove ? b.wk : b.bk;
        if (kingBB != 0) {
            int kingSq = __builtin_ctzll(kingBB);
            if (isSquareAttacked(b, kingSq, !b.whiteToMove)) {
                result.eval = -INF + depth;
            }
        }

        return result;
    }

    Move bestMove = moves[0];
    int bestEval = b.whiteToMove ? -INF : INF;

    for (auto& m : moves) {
        Undo u;
        makeMove(b, m, u);

        int eval = alphaBeta(b, depth - 1, -INF, INF);

        undoMove(b, m, u);

        if (b.whiteToMove && eval > bestEval) {
            bestEval = eval;
            bestMove = m;
        }

        if (!b.whiteToMove && eval < bestEval) {
            bestEval = eval;
            bestMove = m;
        }
    }

    result.bestMove = bestMove;
    result.eval = bestEval;
    return result;
}

Move findBestMove(Board& b, int depth) {
    return searchBestMove(b, depth).bestMove;
}
