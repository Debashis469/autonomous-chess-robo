"""Utility helpers used across the project."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def load_image(path: str | Path) -> np.ndarray:
    """Load an image from disk with a clear error if loading fails."""
    image_path = Path(path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Failed to decode image: {image_path}")
    return image


def resize_keep_ratio(img: np.ndarray, max_side: int = 1600) -> np.ndarray:
    """Resize image so its longest side is max_side while preserving aspect ratio."""
    height, width = img.shape[:2]
    longest = max(height, width)
    if longest <= max_side:
        return img

    scale = max_side / float(longest)
    new_width = max(1, int(round(width * scale)))
    new_height = max(1, int(round(height * scale)))
    return cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)


def algebraic_from_index(row: int, col: int) -> str:
    """
    Convert board matrix index to algebraic notation.

    row 0 -> rank 8, row 7 -> rank 1
    col 0 -> file a, col 7 -> file h
    """
    if not (0 <= row <= 7 and 0 <= col <= 7):
        raise ValueError(f"Invalid row/col for algebraic notation: row={row}, col={col}")

    file_char = chr(ord("a") + col)
    rank_char = str(8 - row)
    return f"{file_char}{rank_char}"


def draw_grid(
    img: np.ndarray,
    board_size: int = 8,
    color: tuple[int, int, int] = (0, 255, 0),
    thickness: int = 1,
) -> np.ndarray:
    """Return a copy of img with board grid lines overlaid."""
    canvas = img.copy()
    height, width = canvas.shape[:2]
    row_edges = np.linspace(0, height, board_size + 1, dtype=int)
    col_edges = np.linspace(0, width, board_size + 1, dtype=int)

    for y in row_edges:
        cv2.line(canvas, (0, y), (width, y), color, thickness)
    for x in col_edges:
        cv2.line(canvas, (x, 0), (x, height), color, thickness)
    return canvas


def ensure_dir(path: str | Path) -> Path:
    """Create a directory if it does not exist and return it as Path."""
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def order_points_clockwise(points: np.ndarray) -> np.ndarray:
    """
    Order a set of 4 points as: top-left, top-right, bottom-right, bottom-left.
    """
    pts = np.asarray(points, dtype=np.float32)
    if pts.shape != (4, 2):
        raise ValueError(f"Expected (4, 2) points, got {pts.shape}")

    ordered = np.zeros((4, 2), dtype=np.float32)
    sums = pts.sum(axis=1)
    diffs = np.diff(pts, axis=1).reshape(-1)

    ordered[0] = pts[np.argmin(sums)]  # top-left
    ordered[2] = pts[np.argmax(sums)]  # bottom-right
    ordered[1] = pts[np.argmin(diffs)]  # top-right
    ordered[3] = pts[np.argmax(diffs)]  # bottom-left
    return ordered
