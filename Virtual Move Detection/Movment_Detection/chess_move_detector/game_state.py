"""Board-state helpers for piece identification using python-chess."""

from __future__ import annotations

from pathlib import Path

import chess


PIECE_NAME_BY_TYPE: dict[int, str] = {
    chess.PAWN: "Pawn",
    chess.KNIGHT: "Knight",
    chess.BISHOP: "Bishop",
    chess.ROOK: "Rook",
    chess.QUEEN: "Queen",
    chess.KING: "King",
}


def init_board(fen: str | None = None) -> chess.Board:
    """Return a board from FEN or a fresh standard board."""
    return chess.Board(fen) if fen else chess.Board()


def load_board_state(state_file: str | Path) -> tuple[chess.Board, bool]:
    """
    Load board state from a FEN file.

    Returns:
        (board, loaded_from_file)
    """
    file_path = Path(state_file)
    if not file_path.exists():
        return init_board(), False

    fen_text = file_path.read_text(encoding="utf-8").strip()
    if not fen_text:
        return init_board(), False

    try:
        return chess.Board(fen_text), True
    except ValueError:
        # Corrupted/invalid file -> fall back to default board.
        return init_board(), False


def save_board_state(board: chess.Board, state_file: str | Path) -> None:
    """Persist current board FEN to disk."""
    file_path = Path(state_file)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(board.fen(), encoding="utf-8")


def _parse_move(move_uci: str) -> chess.Move | None:
    """Safely parse a UCI move string."""
    try:
        return chess.Move.from_uci(move_uci)
    except ValueError:
        return None


def get_piece_name(board: chess.Board, move_uci: str) -> str | None:
    """
    Return readable piece name for the source square of a UCI move.

    If parsing fails or no piece exists on source square, returns None.
    """
    move = _parse_move(move_uci)
    if move is None:
        return None

    piece = board.piece_at(move.from_square)
    if piece is None:
        return None
    return PIECE_NAME_BY_TYPE.get(piece.piece_type)


def is_legal(board: chess.Board, move_uci: str) -> bool:
    """
    Check whether a UCI move is legal, excluding castling/promotion/en passant.
    """
    move = _parse_move(move_uci)
    if move is None:
        return False

    if board.is_castling(move):
        return False
    if board.is_en_passant(move):
        return False
    if move.promotion is not None:
        return False

    return move in board.legal_moves


def apply_move(board: chess.Board, move_uci: str) -> bool:
    """Apply move only if legal. Returns True when pushed."""
    if not is_legal(board, move_uci):
        return False

    move = chess.Move.from_uci(move_uci)
    board.push(move)
    return True
