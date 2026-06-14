#ifndef TYPES_HPP
#define TYPES_HPP

// Piece types
enum Piece {
  PAWN = 0,
  KNIGHT = 1,
  BISHOP = 2,
  ROOK = 3,
  QUEEN = 4,
  KING = 5
};

// Move flags
enum MoveFlag {
  QUIET = 0,
  CAPTURE = 1,
  PROMOTION = 2,
  ENPASSANT = 3,
  CASTLING = 4
};

#endif