import argparse
from pathlib import Path

import cv2
import numpy as np


def order_points(points: np.ndarray) -> np.ndarray:
    sums = points.sum(axis=1)
    diffs = np.diff(points, axis=1).reshape(-1)
    top_left = points[np.argmin(sums)]
    bottom_right = points[np.argmax(sums)]
    top_right = points[np.argmin(diffs)]
    bottom_left = points[np.argmax(diffs)]
    return np.array([top_left, top_right, bottom_right, bottom_left], dtype=np.float32)


def rotate_image(image: np.ndarray, direction: str) -> np.ndarray:
    if direction == "left":
        return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
    if direction == "right":
        return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    return image


def detect_board_corners(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    mask = (gray < 105).astype(np.uint8) * 255
    closed = cv2.morphologyEx(
        mask, cv2.MORPH_CLOSE, np.ones((51, 51), np.uint8), iterations=1
    )
    cleaned = cv2.morphologyEx(
        closed, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8), iterations=1
    )

    contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    best_box = None
    best_area = 0.0

    for contour in contours:
        area = cv2.contourArea(contour)
        if area < 150000:
            continue

        rect = cv2.minAreaRect(contour)
        width, height = rect[1]
        if width == 0 or height == 0:
            continue

        aspect_ratio = max(width, height) / min(width, height)
        if aspect_ratio > 1.4:
            continue

        if area > best_area:
            best_area = area
            best_box = cv2.boxPoints(rect).astype(np.float32)

    if best_box is None:
        raise RuntimeError("Could not detect the chessboard automatically.")

    return order_points(best_box)


def get_output_size(reference_path: Path | None) -> tuple[int, int]:
    if reference_path is not None:
        reference = cv2.imread(str(reference_path))
        if reference is None:
            raise RuntimeError(f"Could not read reference image: {reference_path}")
        return reference.shape[1], reference.shape[0]
    return 628, 620


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rotate and tightly crop a chessboard photo like the sample image."
    )
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", help="Output image path")
    parser.add_argument(
        "--rotate",
        choices=["left", "right", "none"],
        default="right",
        help="Rotate image before cropping",
    )
    parser.add_argument(
        "--reference",
        default="C:/Users/ritur/Downloads/P12.jpeg",
        help="Reference image path used only for output size",
    )
    parser.add_argument(
        "--margin",
        type=int,
        default=4,
        help="Inner margin in pixels for the final crop",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    reference_path = Path(args.reference) if args.reference else None

    image = cv2.imread(str(input_path))
    if image is None:
        raise RuntimeError(f"Could not read input image: {input_path}")

    rotated = rotate_image(image, args.rotate)
    corners = detect_board_corners(rotated)
    output_width, output_height = get_output_size(reference_path)

    margin = args.margin
    destination = np.array(
        [
            [margin, margin],
            [output_width - 1 - margin, margin],
            [output_width - 1 - margin, output_height - 1 - margin],
            [margin, output_height - 1 - margin],
        ],
        dtype=np.float32,
    )

    transform = cv2.getPerspectiveTransform(corners, destination)
    cropped = cv2.warpPerspective(rotated, transform, (output_width, output_height))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    ok = cv2.imwrite(str(output_path), cropped, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    if not ok:
        raise RuntimeError(f"Could not write output image: {output_path}")

    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
