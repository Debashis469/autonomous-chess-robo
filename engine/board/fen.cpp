#include "fen.hpp"

#include <sstream>
#include <vector>

namespace {

bool isPieceChar(char piece) {
    switch (piece) {
        case 'P': case 'N': case 'B': case 'R': case 'Q': case 'K':
        case 'p': case 'n': case 'b': case 'r': case 'q': case 'k':
            return true;
        default:
            return false;
    }
}

void setPiece(Board& b, char piece, int square) {
    uint64_t bit = (1ULL << square);

    switch (piece) {
        case 'P': b.wp |= bit; break;
        case 'N': b.wn |= bit; break;
        case 'B': b.wb |= bit; break;
        case 'R': b.wr |= bit; break;
        case 'Q': b.wq |= bit; break;
        case 'K': b.wk |= bit; break;
        case 'p': b.bp |= bit; break;
        case 'n': b.bn |= bit; break;
        case 'b': b.bb |= bit; break;
        case 'r': b.br |= bit; break;
        case 'q': b.bq |= bit; break;
        case 'k': b.bk |= bit; break;
    }
}

bool isValidCastlingField(const std::string& castling) {
    if (castling == "-") return true;
    if (castling.empty()) return false;

    std::string seen;
    for (char c : castling) {
        if (c != 'K' && c != 'Q' && c != 'k' && c != 'q') return false;
        if (seen.find(c) != std::string::npos) return false;
        seen += c;
    }

    return true;
}

bool isValidEnPassantField(const std::string& enPassant) {
    if (enPassant == "-") return true;
    if (enPassant.size() != 2) return false;

    char file = enPassant[0];
    char rank = enPassant[1];
    return file >= 'a' && file <= 'h' && (rank == '3' || rank == '6');
}

bool hasSingleKings(const Board& board) {
    return __builtin_popcountll(board.wk) == 1 && __builtin_popcountll(board.bk) == 1;
}

} // namespace

bool parseFEN(const std::string& fen, Board& board) {
    std::stringstream ss(fen);
    std::vector<std::string> fields;
    std::string field;

    while (ss >> field) fields.push_back(field);

    board = Board();

    if (fields.size() < 4) return false;

    const std::string& boardPart = fields[0];
    const std::string& turn = fields[1];
    const std::string& castling = fields[2];
    const std::string& enPassant = fields[3];

    if (turn != "w" && turn != "b") return false;
    if (!isValidCastlingField(castling)) return false;
    if (!isValidEnPassantField(enPassant)) return false;

    int rank = 7;
    int fileIndex = 0;

    for (char c : boardPart) {
        if (c == '/') {
            if (fileIndex != 8) return false;
            --rank;
            fileIndex = 0;
            if (rank < 0) return false;
        } else if (c >= '1' && c <= '8') {
            fileIndex += (c - '0');
            if (fileIndex > 8) return false;
        } else if (isPieceChar(c)) {
            if (fileIndex >= 8) return false;
            setPiece(board, c, rank * 8 + fileIndex);
            ++fileIndex;
        } else {
            return false;
        }
    }

    if (rank != 0 || fileIndex != 8) {
        board = Board();
        return false;
    }

    if (!hasSingleKings(board)) {
        board = Board();
        return false;
    }

    board.whiteToMove = (turn == "w");
    board.castlingRights = 0;
    board.enPassantSquare = -1;
    return true;
}
