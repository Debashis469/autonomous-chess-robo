#include "makemove.hpp"

inline void clearBit(uint64_t& bb, int sq) {
    bb &= ~(1ULL << sq);
}

inline void setBit(uint64_t& bb, int sq) {
    bb |= (1ULL << sq);
}

inline void clearSquare(Board& b, int sq) {
    clearBit(b.wp, sq); clearBit(b.wn, sq); clearBit(b.wb, sq);
    clearBit(b.wr, sq); clearBit(b.wq, sq); clearBit(b.wk, sq);

    clearBit(b.bp, sq); clearBit(b.bn, sq); clearBit(b.bb, sq);
    clearBit(b.br, sq); clearBit(b.bq, sq); clearBit(b.bk, sq);
}

inline void setPiece(Board& b, bool white, int piece, int sq) {
    if (white) {
        if (piece == PAWN) setBit(b.wp, sq);
        else if (piece == KNIGHT) setBit(b.wn, sq);
        else if (piece == BISHOP) setBit(b.wb, sq);
        else if (piece == ROOK) setBit(b.wr, sq);
        else if (piece == QUEEN) setBit(b.wq, sq);
        else if (piece == KING) setBit(b.wk, sq);
    } else {
        if (piece == PAWN) setBit(b.bp, sq);
        else if (piece == KNIGHT) setBit(b.bn, sq);
        else if (piece == BISHOP) setBit(b.bb, sq);
        else if (piece == ROOK) setBit(b.br, sq);
        else if (piece == QUEEN) setBit(b.bq, sq);
        else if (piece == KING) setBit(b.bk, sq);
    }
}

void saveState(const Board& b, Undo& u) {
    u.whiteToMove = b.whiteToMove;
    u.castlingRights = b.castlingRights;
    u.enPassantSquare = b.enPassantSquare;

    u.wp = b.wp; u.wn = b.wn; u.wb = b.wb;
    u.wr = b.wr; u.wq = b.wq; u.wk = b.wk;

    u.bp = b.bp; u.bn = b.bn; u.bb = b.bb;
    u.br = b.br; u.bq = b.bq; u.bk = b.bk;
}

void restoreState(Board& b, const Undo& u) {
    b.whiteToMove = u.whiteToMove;
    b.castlingRights = u.castlingRights;
    b.enPassantSquare = u.enPassantSquare;

    b.wp = u.wp; b.wn = u.wn; b.wb = u.wb;
    b.wr = u.wr; b.wq = u.wq; b.wk = u.wk;

    b.bp = u.bp; b.bn = u.bn; b.bb = u.bb;
    b.br = u.br; b.bq = u.bq; b.bk = u.bk;
}

void makeMove(Board& b, const Move& m, Undo& u) {
    saveState(b, u);

    bool white = b.whiteToMove;
    uint64_t fromMask = (1ULL << m.from);
    int captureSq = (m.flag == CAPTURE) ? m.to : -1;

    if (white) {
        if (m.piece == PAWN) b.wp &= ~fromMask;
        else if (m.piece == KNIGHT) b.wn &= ~fromMask;
        else if (m.piece == BISHOP) b.wb &= ~fromMask;
        else if (m.piece == ROOK) b.wr &= ~fromMask;
        else if (m.piece == QUEEN) b.wq &= ~fromMask;
        else if (m.piece == KING) b.wk &= ~fromMask;
    } else {
        if (m.piece == PAWN) b.bp &= ~fromMask;
        else if (m.piece == KNIGHT) b.bn &= ~fromMask;
        else if (m.piece == BISHOP) b.bb &= ~fromMask;
        else if (m.piece == ROOK) b.br &= ~fromMask;
        else if (m.piece == QUEEN) b.bq &= ~fromMask;
        else if (m.piece == KING) b.bk &= ~fromMask;
    }

    if (captureSq != -1) {
        clearSquare(b, captureSq);
    }

    if (m.promotion != -1) {
        setPiece(b, white, m.promotion, m.to);
    } else {
        setPiece(b, white, m.piece, m.to);
    }

    b.castlingRights = 0;
    b.enPassantSquare = -1;
    b.whiteToMove = !b.whiteToMove;
}

void undoMove(Board& b, const Move&, const Undo& u) {
    restoreState(b, u);
}
