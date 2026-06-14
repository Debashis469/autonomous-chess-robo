"""Split a warped board image into 8x8 square images."""

from __future__ import annotations

import numpy as np

from config import BOARD_SIZE


def split_into_squares(board_img: np.ndarray, board_size: int = BOARD_SIZE) -> list[list[np.ndarray]]:
    """Return a board_size x board_size list of square image crops."""
    if board_img is None or board_img.size == 0:
        raise ValueError("Board image is empty.")

    height, width = board_img.shape[:2]
    row_edges = np.linspace(0, height, board_size + 1, dtype=int)
    col_edges = np.linspace(0, width, board_size + 1, dtype=int)

    squares: list[list[np.ndarray]] = []
    for row in range(board_size):
        row_squares: list[np.ndarray] = []
        for col in range(board_size):
            y1, y2 = row_edges[row], row_edges[row + 1]
            x1, x2 = col_edges[col], col_edges[col + 1]
            row_squares.append(board_img[y1:y2, x1:x2].copy())
        squares.append(row_squares)
    return squares
