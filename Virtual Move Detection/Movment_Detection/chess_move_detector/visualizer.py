"""Debug visualization helpers."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from config import BOARD_SIZE
from occupancy_detector import SquareChange
from utils import ensure_dir


def highlight_changed(
    board_img: np.ndarray,
    changed_squares: list[SquareChange],
    board_size: int = BOARD_SIZE,
) -> np.ndarray:
    """Overlay changed square boxes + labels on board image."""
    canvas = board_img.copy()
    height, width = canvas.shape[:2]
    row_edges = np.linspace(0, height, board_size + 1, dtype=int)
    col_edges = np.linspace(0, width, board_size + 1, dtype=int)

    for change in changed_squares:
        y1, y2 = row_edges[change.row], row_edges[change.row + 1]
        x1, x2 = col_edges[change.col], col_edges[change.col + 1]

        cv2.rectangle(canvas, (x1, y1), (x2, y2), (0, 0, 255), 2)
        label = f"{change.algebraic} ({change.score:.0f})"
        cv2.putText(
            canvas,
            label,
            (x1 + 4, min(y2 - 6, y1 + 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

    return canvas


def _make_score_heatmap(score_grid: np.ndarray, target_shape: tuple[int, int]) -> np.ndarray:
    """Create a color heatmap image from 8x8 score grid."""
    normalized = cv2.normalize(score_grid, None, 0, 255, cv2.NORM_MINMAX)
    normalized_u8 = normalized.astype(np.uint8)
    heat_small = cv2.resize(
        normalized_u8,
        (target_shape[1], target_shape[0]),
        interpolation=cv2.INTER_NEAREST,
    )
    return cv2.applyColorMap(heat_small, cv2.COLORMAP_JET)


def save_debug_images(
    output_dir: str | Path,
    prev_board: np.ndarray,
    after_board: np.ndarray,
    changed_squares: list[SquareChange],
    score_grid: np.ndarray | None = None,
) -> dict[str, Path]:
    """Save debug artifacts and return their paths."""
    out = ensure_dir(output_dir)
    saved: dict[str, Path] = {}

    prev_path = out / "prev_warped.jpg"
    after_path = out / "after_warped.jpg"
    cv2.imwrite(str(prev_path), prev_board)
    cv2.imwrite(str(after_path), after_board)
    saved["prev_warped"] = prev_path
    saved["after_warped"] = after_path

    prev_marked = highlight_changed(prev_board, changed_squares)
    after_marked = highlight_changed(after_board, changed_squares)

    prev_marked_path = out / "prev_changed_overlay.jpg"
    after_marked_path = out / "after_changed_overlay.jpg"
    cv2.imwrite(str(prev_marked_path), prev_marked)
    cv2.imwrite(str(after_marked_path), after_marked)
    saved["prev_overlay"] = prev_marked_path
    saved["after_overlay"] = after_marked_path

    panel = np.hstack([prev_marked, after_marked])
    panel_path = out / "comparison_panel.jpg"
    cv2.imwrite(str(panel_path), panel)
    saved["comparison_panel"] = panel_path

    if score_grid is not None:
        heatmap = _make_score_heatmap(score_grid, after_board.shape[:2])
        heatmap_path = out / "square_diff_heatmap.jpg"
        cv2.imwrite(str(heatmap_path), heatmap)
        saved["heatmap"] = heatmap_path

        blended = cv2.addWeighted(after_board, 0.55, heatmap, 0.45, 0.0)
        blended_path = out / "after_heatmap_overlay.jpg"
        cv2.imwrite(str(blended_path), blended)
        saved["after_heatmap_overlay"] = blended_path

    return saved
