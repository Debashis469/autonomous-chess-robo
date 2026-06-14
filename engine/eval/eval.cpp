#include "eval.hpp"

#include "pieces/pawn.hpp"
#include "pieces/knight.hpp"
#include "pieces/bishop.hpp"
#include "pieces/rook.hpp"
#include "pieces/queen.hpp"
#include "pieces/king.hpp"

int evaluate(
  uint64_t wp, uint64_t wn, uint64_t wb,
  uint64_t wr, uint64_t wq, uint64_t wk,
  uint64_t bp, uint64_t bn, uint64_t bb,
  uint64_t br, uint64_t bq, uint64_t bk
) {
  int score = 0;

  // Pawn
  score += evalPawn(wp, bp, true);
  score -= evalPawn(bp, wp, false);

  // Knight
  score += evalKnight(wn, true);
  score -= evalKnight(bn, false);

  // Bishop
  score += evalBishop(wb, true);
  score -= evalBishop(bb, false);

  // Rook
  score += evalRook(wr, wp, bp, true);
  score -= evalRook(br, bp, wp, false);

  // Queen
  score += evalQueen(wq, true);
  score -= evalQueen(bq, false);

  // King
  score += evalKing(wk, wp, true);
  score -= evalKing(bk, bp, false);
  
  // Perspective
  return score ;
}