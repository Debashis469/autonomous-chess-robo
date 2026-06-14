"""Board corner detection and perspective warping."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from config import (
    BLUR_KERNEL,
    BOARD_CONTOUR_MIN_AREA_RATIO,
    CANNY_HIGH,
    CANNY_LOW,
    OUTPUT_DIR,
    WARP_SIZE,
)
from utils import ensure_dir, order_points_clockwise


def _debug_name(filename: str, debug_prefix: str) -> str:
    """Apply optional prefix for debug files."""
    return f"{debug_prefix}{filename}" if debug_prefix else filename


def _save_debug_image(image: np.ndarray, output_dir: str | Path, filename: str) -> None:
    """Persist a debug image to disk."""
    target_dir = ensure_dir(output_dir)
    cv2.imwrite(str(target_dir / filename), image)


def _preprocess_for_contours(gray: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Build contour-friendly masks.

    Returns:
        threshold_mask, edge_mask
    """
    blur = cv2.GaussianBlur(gray, (BLUR_KERNEL, BLUR_KERNEL), 0)

    edges = cv2.Canny(blur, CANNY_LOW, CANNY_HIGH)
    edges = cv2.dilate(edges, np.ones((3, 3), dtype=np.uint8), iterations=1)

    # Texture segmentation: chessboard region has dense gradient structure
    # while floor/background is smoother.
    grad_x = cv2.Sobel(blur, cv2.CV_32F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(blur, cv2.CV_32F, 0, 1, ksize=3)
    grad_mag = cv2.magnitude(grad_x, grad_y)
    grad_mag = cv2.convertScaleAbs(grad_mag)
    grad_mag = cv2.GaussianBlur(grad_mag, (9, 9), 0)

    _, threshold = cv2.threshold(grad_mag, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    min_side = min(gray.shape[:2])
    close_size = max(11, int(round(min_side * 0.02)))
    open_size = max(5, int(round(min_side * 0.007)))
    if close_size % 2 == 0:
        close_size += 1
    if open_size % 2 == 0:
        open_size += 1

    threshold = cv2.morphologyEx(
        threshold,
        cv2.MORPH_CLOSE,
        np.ones((close_size, close_size), dtype=np.uint8),
        iterations=2,
    )
    threshold = cv2.morphologyEx(
        threshold,
        cv2.MORPH_OPEN,
        np.ones((open_size, open_size), dtype=np.uint8),
        iterations=1,
    )

    return threshold, edges


def _angle_deviation_score(points: np.ndarray) -> float:
    """
    Return max absolute cosine of internal quad angles.

    Perfect right angles produce 0. Higher values are less rectangular.
    """
    max_abs_cos = 0.0
    for idx in range(4):
        prev_pt = points[(idx - 1) % 4]
        curr_pt = points[idx]
        next_pt = points[(idx + 1) % 4]
        vec_a = prev_pt - curr_pt
        vec_b = next_pt - curr_pt
        denom = (np.linalg.norm(vec_a) * np.linalg.norm(vec_b)) + 1e-6
        abs_cos = abs(float(np.dot(vec_a, vec_b) / denom))
        max_abs_cos = max(max_abs_cos, abs_cos)
    return max_abs_cos


def _contour_edge_density(edges: np.ndarray, corners: np.ndarray) -> float:
    """Estimate how much edge content exists inside the candidate contour."""
    mask = np.zeros(edges.shape, dtype=np.uint8)
    cv2.fillConvexPoly(mask, corners.astype(np.int32), 255)
    edge_pixels = cv2.countNonZero(cv2.bitwise_and(edges, edges, mask=mask))
    contour_area = max(cv2.contourArea(corners.astype(np.float32)), 1.0)
    return float(edge_pixels) / contour_area


def _candidate_score(
    corners: np.ndarray,
    contour_area: float,
    image_shape: tuple[int, int, int],
    edges: np.ndarray,
) -> float | None:
    """Return score for a board candidate, or None when it fails hard constraints."""
    height, width = image_shape[:2]
    x, y, bound_w, bound_h = cv2.boundingRect(corners.astype(np.int32))
    if bound_w <= 0 or bound_h <= 0:
        return None

    border_margin = max(4, int(min(height, width) * 0.01))
    if (
        np.any(corners[:, 0] <= border_margin)
        or np.any(corners[:, 0] >= (width - 1 - border_margin))
        or np.any(corners[:, 1] <= border_margin)
        or np.any(corners[:, 1] >= (height - 1 - border_margin))
    ):
        return None

    top = np.linalg.norm(corners[1] - corners[0])
    right = np.linalg.norm(corners[2] - corners[1])
    bottom = np.linalg.norm(corners[2] - corners[3])
    left = np.linalg.norm(corners[3] - corners[0])
    est_width = (top + bottom) * 0.5
    est_height = (right + left) * 0.5
    short_side = max(min(est_width, est_height), 1e-6)
    aspect_ratio = max(est_width, est_height) / short_side
    if aspect_ratio > 1.55:
        return None

    bound_aspect = max(bound_w, bound_h) / float(max(min(bound_w, bound_h), 1))
    if bound_aspect > 1.55:
        return None

    angle_deviation = _angle_deviation_score(corners)
    if angle_deviation > 0.45:
        return None

    fill_ratio = contour_area / float(bound_w * bound_h)
    if fill_ratio < 0.35:
        return None

    edge_density = _contour_edge_density(edges, corners)
    if edge_density < 0.01:
        return None

    image_area = float(height * width)
    area_ratio = contour_area / image_area

    return (
        (area_ratio * 5.0)
        + (1.6 - min(aspect_ratio, 1.6))
        + (1.0 - min(angle_deviation, 1.0))
        + min(fill_ratio, 1.0)
        + min(edge_density * 15.0, 1.5)
    )


def detect_board_corners(
    img: np.ndarray,
    min_area_ratio: float = BOARD_CONTOUR_MIN_AREA_RATIO,
    debug: bool = False,
    output_dir: str | Path = OUTPUT_DIR,
    debug_prefix: str = "",
) -> np.ndarray:
    """
    Detect board corners as 4 ordered points:
    top-left, top-right, bottom-right, bottom-left.
    """
    if img is None or img.size == 0:
        raise ValueError("Input image for board detection is empty.")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    threshold, edges = _preprocess_for_contours(gray)

    contour_mask = threshold.copy()

    contours, _ = cv2.findContours(contour_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    image_area = float(img.shape[0] * img.shape[1])
    min_area = image_area * min_area_ratio

    best_corners: np.ndarray | None = None
    best_contour: np.ndarray | None = None
    best_score = -np.inf

    for contour in contours:
        contour_area = cv2.contourArea(contour)
        if contour_area < min_area:
            break

        perimeter = cv2.arcLength(contour, True)
        if perimeter <= 0.0:
            continue

        quad: np.ndarray | None = None
        for eps_ratio in (0.015, 0.02, 0.03):
            approx = cv2.approxPolyDP(contour, eps_ratio * perimeter, True)
            if len(approx) == 4 and cv2.isContourConvex(approx):
                quad = approx.reshape(4, 2).astype(np.float32)
                break

        if quad is None:
            continue

        ordered_corners = order_points_clockwise(quad)
        score = _candidate_score(ordered_corners, contour_area, img.shape, edges)
        if score is None:
            continue

        if score > best_score:
            best_score = score
            best_corners = ordered_corners
            best_contour = contour

    contour_vis = img.copy()

    if best_corners is None:
        print("Board detection failed, using fallback.")
        height, width = img.shape[:2]
        best_corners = np.array(
            [
                [0, 0],
                [width - 1, 0],
                [width - 1, height - 1],
                [0, height - 1],
            ],
            dtype=np.float32,
        )
        cv2.polylines(contour_vis, [best_corners.astype(np.int32)], True, (0, 0, 255), 3)
        cv2.putText(
            contour_vis,
            "fallback",
            (16, 32),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 0, 255),
            2,
            lineType=cv2.LINE_AA,
        )
    else:
        if best_contour is not None:
            cv2.drawContours(contour_vis, [best_contour], -1, (0, 255, 255), 2)
        cv2.polylines(contour_vis, [best_corners.astype(np.int32)], True, (0, 255, 0), 3)
        for index, point in enumerate(best_corners.astype(np.int32)):
            cv2.circle(contour_vis, tuple(point), 8, (255, 0, 0), -1)
            cv2.putText(
                contour_vis,
                str(index),
                (point[0] + 10, point[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
                lineType=cv2.LINE_AA,
            )

    if debug:
        _save_debug_image(threshold, output_dir, _debug_name("threshold.jpg", debug_prefix))
        _save_debug_image(edges, output_dir, _debug_name("edges.jpg", debug_prefix))
        _save_debug_image(
            contour_vis,
            output_dir,
            _debug_name("detected_contour.jpg", debug_prefix),
        )

    return best_corners


def warp_board(img: np.ndarray, corners: np.ndarray, size: int = WARP_SIZE) -> np.ndarray:
    """Apply perspective transform to produce a square top-down board image."""
    if img is None or img.size == 0:
        raise ValueError("Input image for warping is empty.")

    ordered_corners = order_points_clockwise(corners.astype(np.float32))
    destination = np.array(
        [
            [0, 0],
            [size - 1, 0],
            [size - 1, size - 1],
            [0, size - 1],
        ],
        dtype=np.float32,
    )

    transform = cv2.getPerspectiveTransform(ordered_corners, destination)
    return cv2.warpPerspective(img, transform, (size, size))


def detect_and_crop_board(
    img: np.ndarray,
    size: int = WARP_SIZE,
    debug: bool = False,
    output_dir: str | Path = OUTPUT_DIR,
    debug_prefix: str = "",
) -> np.ndarray:
    """Detect board corners, then return the warped square board image."""
    corners = detect_board_corners(
        img=img,
        debug=debug,
        output_dir=output_dir,
        debug_prefix=debug_prefix,
    )
    warped = warp_board(img, corners, size=size)
    if debug:
        _save_debug_image(warped, output_dir, _debug_name("warped_board.jpg", debug_prefix))
    return warped


def align_board_to_reference(
    reference_board: np.ndarray,
    target_board: np.ndarray,
) -> tuple[np.ndarray, bool]:
    """
    Align target_board to reference_board using ECC translation alignment.

    This reduces false changes from tiny camera shifts between frames.
    """
    ref_gray = cv2.cvtColor(reference_board, cv2.COLOR_BGR2GRAY)
    tgt_gray = cv2.cvtColor(target_board, cv2.COLOR_BGR2GRAY)

    warp_matrix = np.eye(2, 3, dtype=np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 60, 1e-5)

    try:
        cv2.findTransformECC(
            templateImage=ref_gray,
            inputImage=tgt_gray,
            warpMatrix=warp_matrix,
            motionType=cv2.MOTION_TRANSLATION,
            criteria=criteria,
        )
    except cv2.error:
        return target_board, False

    aligned = cv2.warpAffine(
        target_board,
        warp_matrix,
        (reference_board.shape[1], reference_board.shape[0]),
        flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP,
        borderMode=cv2.BORDER_REPLICATE,
    )
    return aligned, True
