#include "board_to_fen.hpp"

#include <string>

using namespace std;


static char getPieceAt(
    const Board& b,
    int sq
) {

    uint64_t mask = (1ULL << sq);

    if (b.wp & mask) return 'P';
    if (b.wn & mask) return 'N';
    if (b.wb & mask) return 'B';
    if (b.wr & mask) return 'R';
    if (b.wq & mask) return 'Q';
    if (b.wk & mask) return 'K';

    if (b.bp & mask) return 'p';
    if (b.bn & mask) return 'n';
    if (b.bb & mask) return 'b';
    if (b.br & mask) return 'r';
    if (b.bq & mask) return 'q';
    if (b.bk & mask) return 'k';

    return '.';
}


string boardToFEN(
    const Board& b
) {

    string fen;

    for (int rank = 7; rank >= 0; rank--) {

        int empty = 0;

        for (int file = 0; file < 8; file++) {

            int sq = rank * 8 + file;

            char piece =
                getPieceAt(b, sq);

            if (piece == '.') {

                empty++;
            }
            else {

                if (empty > 0) {

                    fen += to_string(empty);

                    empty = 0;
                }

                fen += piece;
            }
        }

        if (empty > 0) {
            fen += to_string(empty);
        }

        if (rank > 0) {
            fen += "/";
        }
    }


    // side to move
    fen += b.whiteToMove ? " w " : " b ";


    // castling
    fen += "- ";


    // en passant
    fen += "- ";


    // halfmove/fullmove
    fen += "0 1";

    return fen;
}