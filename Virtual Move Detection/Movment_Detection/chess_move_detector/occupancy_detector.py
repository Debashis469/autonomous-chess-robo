"""Detect changed squares using classical computer-vision difference metrics."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from config import (
    CHANGE_SCORE_RELATIVE_MIN,
    DIFF_THRESHOLD,
    MAX_CHANGED_SQUARES,
    MIN_CHANGE_AREA,
    MIN_MEAN_DIFF,
    SQUARE_INNER_CROP_RATIO,
)
from utils import algebraic_from_index


@dataclass(frozen=True)
class SquareChange:
    """Per-square change statistics between prev and after board states."""

    row: int
    col: int
    changed_pixels: int
    changed_ratio: float
    mean_diff: float
    score: float

    @property
    def algebraic(self) -> str:
        return algebraic_from_index(self.row, self.col)


def _as_gray(square_img: np.ndarray) -> np.ndarray:
    if square_img.ndim == 2:
        return square_img
    return cv2.cvtColor(square_img, cv2.COLOR_BGR2GRAY)


def _crop_inner(gray: np.ndarray, crop_ratio: float = SQUARE_INNER_CROP_RATIO) -> np.ndarray:
    """Crop a centered region to reduce border/perspective noise."""
    if crop_ratio <= 0:
        return gray

    h, w = gray.shape[:2]
    margin_h = int(h * crop_ratio)
    margin_w = int(w * crop_ratio)
    y1, y2 = margin_h, h - margin_h
    x1, x2 = margin_w, w - margin_w
    if y2 <= y1 or x2 <= x1:
        return gray
    return gray[y1:y2, x1:x2]


def square_change_score(
    prev_sq: np.ndarray,
    after_sq: np.ndarray,
    diff_threshold: int = DIFF_THRESHOLD,
) -> tuple[int, float, float, float]:
    """
    Score how much a square changed.

    Returns:
        changed_pixels, changed_ratio, mean_diff, score
    """
    prev_gray = _crop_inner(_as_gray(prev_sq))
    after_gray = _crop_inner(_as_gray(after_sq))

    # Gentle blur makes tiny in-square shifts less sensitive while preserving move-level changes.
    prev_gray = cv2.GaussianBlur(prev_gray, (3, 3), 0)
    after_gray = cv2.GaussianBlur(after_gray, (3, 3), 0)

    diff = cv2.absdiff(prev_gray, after_gray)
    _, binary = cv2.threshold(diff, diff_threshold, 255, cv2.THRESH_BINARY)

    kernel = np.ones((3, 3), dtype=np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)

    changed_pixels = int(cv2.countNonZero(binary))
    total_pixels = binary.size if binary.size > 0 else 1
    changed_ratio = changed_pixels / float(total_pixels)
    mean_diff = float(np.mean(diff))

    # Weighted blend of area and intensity deltas.
    score = changed_pixels + (mean_diff * 12.0)
    return changed_pixels, changed_ratio, mean_diff, score


def compute_score_grid(
    prev_squares: list[list[np.ndarray]],
    after_squares: list[list[np.ndarray]],
    diff_threshold: int = DIFF_THRESHOLD,
) -> np.ndarray:
    """Compute raw change scores for all 64 squares as an 8x8 float grid."""
    board_size = len(prev_squares)
    score_grid = np.zeros((board_size, board_size), dtype=np.float32)
    for row in range(board_size):
        for col in range(board_size):
            _, _, _, score = square_change_score(
                prev_squares[row][col],
                after_squares[row][col],
                diff_threshold=diff_threshold,
            )
            score_grid[row, col] = float(score)
    return score_grid


def detect_changed_squares(
    prev_squares: list[list[np.ndarray]],
    after_squares: list[list[np.ndarray]],
    diff_threshold: int = DIFF_THRESHOLD,
    min_change_area: int = MIN_CHANGE_AREA,
    min_mean_diff: float = MIN_MEAN_DIFF,
    relative_score_min: float = CHANGE_SCORE_RELATIVE_MIN,
    max_changed_squares: int = MAX_CHANGED_SQUARES,
) -> list[SquareChange]:
    """
    Detect changed squares and return them sorted by descending score.
    """
    if len(prev_squares) != len(after_squares):
        raise ValueError("prev_squares and after_squares must have the same board size.")

    all_changes: list[SquareChange] = []
    for row in range(len(prev_squares)):
        for col in range(len(prev_squares[row])):
            changed_pixels, changed_ratio, mean_diff, score = square_change_score(
                prev_squares[row][col],
                after_squares[row][col],
                diff_threshold=diff_threshold,
            )
            all_changes.append(
                SquareChange(
                    row=row,
                    col=col,
                    changed_pixels=changed_pixels,
                    changed_ratio=changed_ratio,
                    mean_diff=mean_diff,
                    score=score,
                )
            )

    all_changes.sort(key=lambda item: item.score, reverse=True)

    filtered = [
        item
        for item in all_changes
        if item.changed_pixels >= min_change_area and item.mean_diff >= min_mean_diff
    ]

    if not filtered:
        return []

    strongest = max(item.score for item in filtered)
    relative_cutoff = strongest * max(0.0, float(relative_score_min))
    filtered = [item for item in filtered if item.score >= relative_cutoff]
    return filtered[:max_changed_squares]


def estimate_occupancy(square_img: np.ndarray) -> float:
    """
    Estimate how occupied a square looks (higher generally means more piece content).
    """
    gray = _as_gray(square_img)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    h, w = blur.shape
    margin_h = max(1, int(h * 0.15))
    margin_w = max(1, int(w * 0.15))
    center = blur[margin_h : h - margin_h, margin_w : w - margin_w]
    if center.size == 0:
        center = blur

    std_dev = float(np.std(center))
    laplacian_var = float(cv2.Laplacian(center, cv2.CV_64F).var())
    edges = cv2.Canny(center, 40, 120)
    edge_ratio = float(np.count_nonzero(edges)) / float(edges.size if edges.size > 0 else 1)

    return (std_dev * 0.9) + (min(laplacian_var, 3000.0) * 0.02) + (edge_ratio * 120.0)
