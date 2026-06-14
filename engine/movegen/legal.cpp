#include "legal.hpp"
#include "movegen.hpp"
#include "../move/makemove.hpp"
#include <cmath>

using namespace std;

// ================= HELPERS =================

inline uint64_t getWhite(const Board& b) {
  return b.wp | b.wn | b.wb | b.wr | b.wq | b.wk;
}

inline uint64_t getBlack(const Board& b) {
  return b.bp | b.bn | b.bb | b.br | b.bq | b.bk;
}

// ================= ATTACK DETECTION =================

bool isSquareAttacked(const Board& b, int sq, bool byWhite) {
  uint64_t pawns = byWhite ? b.wp : b.bp;
  uint64_t knights = byWhite ? b.wn : b.bn;
  uint64_t bishops = byWhite ? b.wb : b.bb;
  uint64_t rooks = byWhite ? b.wr : b.br;
  uint64_t queens = byWhite ? b.wq : b.bq;
  uint64_t king = byWhite ? b.wk : b.bk;

  // ================= PAWNS =================
  const int whitePawnOffsets[2] = {-7, -9};
  const int blackPawnOffsets[2] = {7, 9};

  const int* pawnOffsets = byWhite ? whitePawnOffsets : blackPawnOffsets;

  for (int i = 0; i < 2; i++) {
    int off = pawnOffsets[i];
    int from = sq + off;

    if (from >= 0 && from < 64) {
      if (abs((from % 8) - (sq % 8)) == 1) {
        if (pawns & (1ULL << from)) return true;
      }
    }
  }

    // ================= KNIGHTS =================
    int knightOffsets[8] = {17,15,10,6,-17,-15,-10,-6};

    for (int off : knightOffsets) {
        int from = sq + off;
        if (from >= 0 && from < 64) {
            if (abs((from % 8) - (sq % 8)) <= 2) {
                if (knights & (1ULL << from)) return true;
            }
        }
    }

    // ================= KING =================
    int kingOffsets[8] = {8,-8,1,-1,9,-9,7,-7};

    for (int off : kingOffsets) {
        int from = sq + off;
        if (from >= 0 && from < 64) {
            if (abs((from % 8) - (sq % 8)) <= 1) {
                if (king & (1ULL << from)) return true;
            }
        }
    }

    // ================= SLIDING =================

    int bishopDirs[4] = {9,7,-9,-7};
    int rookDirs[4]   = {8,-8,1,-1};

    // bishop / queen
    for (int d : bishopDirs) {
        int to = sq;
        while (true) {
            int prev = to;
            to += d;

            if (to < 0 || to >= 64) break;

            if (abs((to % 8) - (prev % 8)) != 1) break;

            uint64_t bit = (1ULL << to);

            if (bit & (byWhite ? getWhite(b) : getBlack(b))) {
                if ((bishops | queens) & bit) return true;
                break;
            }

            if (bit & (byWhite ? getBlack(b) : getWhite(b))) break;
        }
    }

    // rook / queen
    for (int d : rookDirs) {
        int to = sq;
        while (true) {
            int prev = to;
            to += d;

            if (to < 0 || to >= 64) break;

            if ((d == 1 || d == -1) && abs((to % 8) - (prev % 8)) != 1)  break;

            uint64_t bit = (1ULL << to);

            if (bit & (byWhite ? getWhite(b) : getBlack(b))) {
              if ((rooks | queens) & bit) return true;
              break;
            }

            if (bit & (byWhite ? getBlack(b) : getWhite(b))) break;
        }
    }

    return false;
}

// ================= LEGAL MOVES =================

vector<Move> generateLegalMoves(Board& b) {
    vector<Move> moves = generateMoves(b);
    vector<Move> legalMoves;

    for (auto& m : moves) {
        Undo u;
        makeMove(b, m, u);

        // find king square AFTER move
        uint64_t kingBB = b.whiteToMove ? b.bk : b.wk;
        if (kingBB == 0) {
            undoMove(b, m, u);
            continue;
        }

        int kingSq = __builtin_ctzll(kingBB);

        // check if opponent attacks king
        if (!isSquareAttacked(b, kingSq, b.whiteToMove)) {
            legalMoves.push_back(m);
        }

        undoMove(b, m, u);
    }

    return legalMoves;
}
