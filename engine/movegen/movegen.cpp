#include "movegen.hpp"

#include <cmath>

using namespace std;

inline int popLSB(uint64_t& bb) {
    int sq = __builtin_ctzll(bb);
    bb &= bb - 1;
    return sq;
}

inline uint64_t getWhite(const Board& b) {
    return b.wp | b.wn | b.wb | b.wr | b.wq | b.wk;
}

inline uint64_t getBlack(const Board& b) {
    return b.bp | b.bn | b.bb | b.br | b.bq | b.bk;
}

inline bool isPromotionRank(int rank, bool white) {
    return white ? rank == 6 : rank == 1;
}

void addPromotionMoves(vector<Move>& moves, int from, int to, bool capture) {
    const int promos[4] = {QUEEN};  /// for simplicity we have allowed only queen promotion

    for (int promo : promos) {
        moves.emplace_back(from, to, PAWN, capture ? PAWN : -1, promo,
                           capture ? CAPTURE : PROMOTION);
    }
}

void generatePawnMoves(const Board& b, vector<Move>& moves) {
    bool white = b.whiteToMove;

    uint64_t pawns = white ? b.wp : b.bp;
    uint64_t own = white ? getWhite(b) : getBlack(b);
    uint64_t opp = white ? getBlack(b) : getWhite(b);
    uint64_t all = own | opp;

    while (pawns) {
        int sq = popLSB(pawns);
        int rank = sq / 8;

        int dir = white ? 8 : -8;
        int to = sq + dir;

        if (to >= 0 && to < 64 && !(all & (1ULL << to))) {
            if (isPromotionRank(rank, white)) {
                addPromotionMoves(moves, sq, to, false);
            } else {
                moves.emplace_back(sq, to, PAWN);

                if (white && rank == 1) {
                    int to2 = sq + 16;
                    if (to2 < 64 && !(all & (1ULL << to2))) {
                        moves.emplace_back(sq, to2, PAWN);
                    }
                }

                if (!white && rank == 6) {
                    int to2 = sq - 16;
                    if (to2 >= 0 && !(all & (1ULL << to2))) {
                        moves.emplace_back(sq, to2, PAWN);
                    }
                }
            }
        }

        int caps[2] = {sq + (white ? 7 : -7), sq + (white ? 9 : -9)};

        for (int c : caps) {
            if (c < 0 || c >= 64) continue;
            if (abs((c % 8) - (sq % 8)) != 1) continue;

            if (opp & (1ULL << c)) {
                if (isPromotionRank(rank, white)) {
                    addPromotionMoves(moves, sq, c, true);
                } else {
                    moves.emplace_back(sq, c, PAWN, PAWN, -1, CAPTURE);
                }
            }
        }
    }
}

const int knightOffsets[8] = {17, 15, 10, 6, -17, -15, -10, -6};

void generateKnightMoves(const Board& b, vector<Move>& moves) {
    bool white = b.whiteToMove;

    uint64_t knights = white ? b.wn : b.bn;
    uint64_t own = white ? getWhite(b) : getBlack(b);
    uint64_t opp = white ? getBlack(b) : getWhite(b);

    while (knights) {
        int sq = popLSB(knights);

        for (int off : knightOffsets) {
            int to = sq + off;

            if (to < 0 || to >= 64) continue;
            if (abs((to % 8) - (sq % 8)) > 2) continue;
            if (own & (1ULL << to)) continue;

            if (opp & (1ULL << to)) {
                moves.emplace_back(sq, to, KNIGHT, KNIGHT, -1, CAPTURE);
            } else {
                moves.emplace_back(sq, to, KNIGHT);
            }
        }
    }
}

const int kingOffsets[8] = {8, -8, 1, -1, 9, -9, 7, -7};

void generateKingMoves(const Board& b, vector<Move>& moves) {
    bool white = b.whiteToMove;

    uint64_t king = white ? b.wk : b.bk;
    if (king == 0) return;

    int sq = __builtin_ctzll(king);

    uint64_t own = white ? getWhite(b) : getBlack(b);
    uint64_t opp = white ? getBlack(b) : getWhite(b);

    for (int off : kingOffsets) {
        int to = sq + off;

        if (to < 0 || to >= 64) continue;
        if (abs((to % 8) - (sq % 8)) > 1) continue;
        if (own & (1ULL << to)) continue;

        if (opp & (1ULL << to)) {
            moves.emplace_back(sq, to, KING, KING, -1, CAPTURE);
        } else {
            moves.emplace_back(sq, to, KING);
        }
    }
}

void generateSliding(const Board& b, vector<Move>& moves,
                     uint64_t pieces, const int dirs[], int dirCount, int pieceType) {
    bool white = b.whiteToMove;

    uint64_t own = white ? getWhite(b) : getBlack(b);
    uint64_t opp = white ? getBlack(b) : getWhite(b);

    while (pieces) {
        int sq = popLSB(pieces);

        for (int i = 0; i < dirCount; i++) {
            int d = dirs[i];
            int to = sq;

            while (true) {
                int prev = to;
                to += d;

                if (to < 0 || to >= 64) break;

                int fileDiff = abs((to % 8) - (prev % 8));
                if ((d == 1 || d == -1) && fileDiff != 1) break;
                if ((d == 9 || d == -9 || d == 7 || d == -7) && fileDiff != 1) break;
                if (own & (1ULL << to)) break;

                if (opp & (1ULL << to)) {
                    moves.emplace_back(sq, to, pieceType, pieceType, -1, CAPTURE);
                    break;
                }

                moves.emplace_back(sq, to, pieceType);
            }
        }
    }
}

vector<Move> generateMoves(const Board& b) {
    vector<Move> moves;

    generatePawnMoves(b, moves);
    generateKnightMoves(b, moves);

    int bishopDirs[4] = {9, 7, -9, -7};
    int rookDirs[4] = {8, -8, 1, -1};
    int queenDirs[8] = {8, -8, 1, -1, 9, 7, -9, -7};

    generateSliding(b, moves, b.whiteToMove ? b.wb : b.bb, bishopDirs, 4, BISHOP);
    generateSliding(b, moves, b.whiteToMove ? b.wr : b.br, rookDirs, 4, ROOK);
    generateSliding(b, moves, b.whiteToMove ? b.wq : b.bq, queenDirs, 8, QUEEN);
    generateKingMoves(b, moves);

    return moves;
}
