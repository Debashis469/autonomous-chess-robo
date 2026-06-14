import cv2
import numpy as np


def _order_points(pts):
    """Return points in top-left, top-right, bottom-right, bottom-left order."""
    rect = np.zeros((4, 2), dtype="float32")

    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    return rect


def _four_point_transform(image, pts):
    """Apply perspective transform from a 4-point contour."""
    rect = _order_points(pts.astype("float32"))
    (tl, tr, br, bl) = rect

    side_lengths = [
        np.linalg.norm(br - bl),
        np.linalg.norm(tr - tl),
        np.linalg.norm(tr - br),
        np.linalg.norm(tl - bl),
    ]
    side = int(round(np.mean(side_lengths)))

    # Ignore invalid tiny transforms.
    if side < 40:
        return None

    dst = np.array(
        [
            [0, 0],
            [side - 1, 0],
            [side - 1, side - 1],
            [0, side - 1],
        ],
        dtype="float32",
    )

    matrix = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(image, matrix, (side, side))


def _green_ring_ratio(green_mask, x1, y1, x2, y2):
    """
    Measure how much green surrounds a candidate board box.
    The board usually sits on green cloth, so a greener outer ring is a good signal.
    """
    h, w = green_mask.shape
    box_w = max(1, x2 - x1)
    box_h = max(1, y2 - y1)
    pad = max(8, int(min(box_w, box_h) * 0.08))

    ex1 = max(0, x1 - pad)
    ey1 = max(0, y1 - pad)
    ex2 = min(w, x2 + pad)
    ey2 = min(h, y2 + pad)

    ring = np.zeros_like(green_mask, dtype=np.uint8)
    ring[ey1:ey2, ex1:ex2] = 1
    ring[y1:y2, x1:x2] = 0

    ring_pixels = np.count_nonzero(ring)
    if ring_pixels == 0:
        return 0.0

    return float(np.count_nonzero(green_mask[ring > 0])) / float(ring_pixels)


def _find_green_background_quad(image):
    """
    Detect the board as the main non-green square resting on the green cloth.
    This path is tuned for the overhead capture setup shown by the user.
    """
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    green_mask = cv2.inRange(
        hsv,
        np.array([35, 45, 35], dtype=np.uint8),
        np.array([95, 255, 255], dtype=np.uint8),
    )

    non_green = 255 - green_mask
    non_green = cv2.morphologyEx(
        non_green, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8), iterations=1
    )
    non_green = cv2.morphologyEx(
        non_green, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8), iterations=1
    )

    contours_info = cv2.findContours(non_green, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = contours_info[0] if len(contours_info) == 2 else contours_info[1]

    h, w = image.shape[:2]
    image_area = float(h * w)
    best_score = -1e9
    best_quad = None

    for cnt in contours:
        area = cv2.contourArea(cnt)
        area_ratio = area / image_area
        if area_ratio < 0.05 or area_ratio > 0.75:
            continue

        rect = cv2.minAreaRect(cnt)
        width, height = rect[1]
        if width <= 0 or height <= 0:
            continue

        aspect = max(width, height) / max(1.0, min(width, height))
        if aspect > 1.35:
            continue

        box_area = float(width * height)
        rectangularity = area / max(1.0, box_area)
        if rectangularity < 0.75:
            continue

        pts = cv2.boxPoints(rect).astype("float32")
        x_min, y_min = np.floor(pts.min(axis=0)).astype(int)
        x_max, y_max = np.ceil(pts.max(axis=0)).astype(int)

        border_touch = 0
        margin = 3
        if x_min <= margin:
            border_touch += 1
        if y_min <= margin:
            border_touch += 1
        if x_max >= w - 1 - margin:
            border_touch += 1
        if y_max >= h - 1 - margin:
            border_touch += 1
        if border_touch >= 2:
            continue

        ring_green = _green_ring_ratio(green_mask, x_min, y_min, x_max, y_max)
        if ring_green < 0.18:
            continue

        center_x, center_y = rect[0]
        center_dist = ((center_x - (w * 0.5)) ** 2 + (center_y - (h * 0.5)) ** 2) ** 0.5
        center_penalty = center_dist / max(h, w)

        score = 0.0
        score += area_ratio * 150.0
        score += rectangularity * 35.0
        score += ring_green * 30.0
        score -= abs(np.log(aspect)) * 50.0
        score -= border_touch * 25.0
        score -= center_penalty * 8.0

        if score > best_score:
            best_score = score
            best_quad = pts

    return best_quad


def _cluster_line_positions(items, tolerance):
    """Merge nearby Hough line positions into weighted clusters."""
    if not items:
        return []

    clusters = []
    for pos, support in sorted(items, key=lambda item: item[0]):
        if not clusters or abs(pos - clusters[-1]["center"]) > tolerance:
            clusters.append({"positions": [pos], "supports": [support]})
        else:
            clusters[-1]["positions"].append(pos)
            clusters[-1]["supports"].append(support)

        cluster = clusters[-1]
        weighted_total = sum(
            position * weight for position, weight in zip(cluster["positions"], cluster["supports"])
        )
        total_support = sum(cluster["supports"])
        cluster["center"] = weighted_total / max(1.0, total_support)
        cluster["support"] = total_support

    return clusters


def _find_axis_aligned_board_box(image):
    """
    Fallback for near top-down frames:
    detect the full board box from long horizontal/vertical board lines.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 25, 90)

    h, w = image.shape[:2]
    min_line_length = max(120, min(h, w) // 4)
    lines = cv2.HoughLinesP(
        edges,
        1,
        np.pi / 180,
        threshold=40,
        minLineLength=min_line_length,
        maxLineGap=25,
    )
    if lines is None:
        return None

    horizontal_tolerance = max(8, h // 80)
    vertical_tolerance = max(8, w // 100)

    horizontal_lines = []
    vertical_lines = []

    for line in lines[:, 0, :]:
        x1, y1, x2, y2 = map(int, line)
        dx = x2 - x1
        dy = y2 - y1

        if abs(dy) <= horizontal_tolerance and abs(dx) >= min_line_length:
            horizontal_lines.append((((y1 + y2) * 0.5), abs(dx)))
        if abs(dx) <= vertical_tolerance and abs(dy) >= min_line_length:
            vertical_lines.append((((x1 + x2) * 0.5), abs(dy)))

    vertical_clusters = _cluster_line_positions(vertical_lines, tolerance=max(8, w // 70))
    horizontal_clusters = _cluster_line_positions(horizontal_lines, tolerance=max(8, h // 70))

    # Keep only center-ish line groups to ignore floor/background edges.
    vertical_clusters = [
        cluster for cluster in vertical_clusters if (0.08 * w) <= cluster["center"] <= (0.92 * w)
    ]
    horizontal_clusters = [
        cluster for cluster in horizontal_clusters if (0.05 * h) <= cluster["center"] <= (0.95 * h)
    ]

    if len(vertical_clusters) < 2 or len(horizontal_clusters) < 2:
        return None

    strong_vertical_positions = sorted(
        cluster["center"] for cluster in vertical_clusters if cluster["support"] >= min_line_length
    )
    strong_horizontal_positions = sorted(
        cluster["center"] for cluster in horizontal_clusters if cluster["support"] >= min_line_length
    )

    cell_diffs = []
    max_cell_gap = max(70, min(h, w) // 6)
    for positions in (strong_vertical_positions, strong_horizontal_positions):
        for index in range(len(positions) - 1):
            diff = positions[index + 1] - positions[index]
            if 18 <= diff <= max_cell_gap:
                cell_diffs.append(diff)

    if len(cell_diffs) < 4:
        return None

    cell_size = float(np.median(cell_diffs))

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    green_mask = cv2.inRange(
        hsv,
        np.array([35, 45, 35], dtype=np.uint8),
        np.array([95, 255, 255], dtype=np.uint8),
    )

    best_score = -1e9
    best_box = None

    for left_index in range(len(vertical_clusters)):
        for right_index in range(left_index + 1, len(vertical_clusters)):
            x1 = vertical_clusters[left_index]["center"]
            x2 = vertical_clusters[right_index]["center"]
            box_width = x2 - x1

            if box_width < (0.45 * w):
                continue

            for top_index in range(len(horizontal_clusters)):
                for bottom_index in range(top_index + 1, len(horizontal_clusters)):
                    y1 = horizontal_clusters[top_index]["center"]
                    y2 = horizontal_clusters[bottom_index]["center"]
                    box_height = y2 - y1

                    if box_height < (0.45 * h):
                        continue

                    width_ratio = box_width / cell_size
                    height_ratio = box_height / cell_size

                    ratio_penalty = (
                        min(abs(width_ratio - 9.0), abs(width_ratio - 8.0)) * 2.0
                        + min(abs(height_ratio - 9.0), abs(height_ratio - 8.0)) * 2.0
                    )
                    if ratio_penalty > 2.5:
                        continue

                    aspect = max(box_width, box_height) / max(1.0, min(box_width, box_height))
                    if aspect > 1.25:
                        continue

                    center_x = (x1 + x2) * 0.5
                    center_y = (y1 + y2) * 0.5
                    center_dist = ((center_x - (w * 0.5)) ** 2 + (center_y - (h * 0.5)) ** 2) ** 0.5
                    center_penalty = center_dist / max(h, w)
                    area_ratio = (box_width * box_height) / float(h * w)

                    ix1 = int(round(x1))
                    iy1 = int(round(y1))
                    ix2 = int(round(x2))
                    iy2 = int(round(y2))

                    ring_green = _green_ring_ratio(green_mask, ix1, iy1, ix2, iy2)
                    support = (
                        vertical_clusters[left_index]["support"]
                        + vertical_clusters[right_index]["support"]
                        + horizontal_clusters[top_index]["support"]
                        + horizontal_clusters[bottom_index]["support"]
                    )

                    score = 0.0
                    score += area_ratio * 180.0
                    score += ring_green * 18.0
                    score += (support / max(h, w)) * 0.15
                    score -= aspect * 5.0
                    score -= center_penalty * 8.0
                    score -= ratio_penalty * 10.0

                    if score > best_score:
                        best_score = score
                        best_box = np.array(
                            [
                                [ix1, iy1],
                                [ix2, iy1],
                                [ix2, iy2],
                                [ix1, iy2],
                            ],
                            dtype="float32",
                        )

    return best_box


def _refine_checkerboard_region(image):
    """
    Final trim step:
    find the strongest 8x8 checker-like square region and crop to it.
    This helps remove extra background when the first warp is slightly loose.
    """
    if image is None or image.size == 0:
        return image

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float32)
    h, w = gray.shape
    min_side = min(h, w)

    # If result is already tiny, skip refinement.
    if min_side < 120:
        return image

    integral = cv2.integral(gray)
    checker_mask = ((np.indices((8, 8)).sum(axis=0) % 2) * 2 - 1).astype(np.float32)

    def rect_mean(x1, y1, x2, y2):
        area = max(1, (x2 - x1) * (y2 - y1))
        total = (
            integral[y2, x2]
            - integral[y1, x2]
            - integral[y2, x1]
            + integral[y1, x1]
        )
        return total / area

    best = None
    size_start = int(min_side * 0.45)
    size_end = int(min_side * 0.95)

    for size in range(size_start, size_end + 1, 8):
        step = max(6, size // 28)

        for y in range(0, h - size + 1, step):
            for x in range(0, w - size + 1, step):
                cell = size // 8
                side = cell * 8
                if cell < 6:
                    continue
                if x + side > w or y + side > h:
                    continue

                means = np.zeros((8, 8), dtype=np.float32)
                for r in range(8):
                    for c in range(8):
                        x1 = x + c * cell
                        y1 = y + r * cell
                        means[r, c] = rect_mean(x1, y1, x1 + cell, y1 + cell)

                # Suppress illumination gradients so checker pattern dominates.
                means = (
                    means
                    - means.mean(axis=0, keepdims=True) * 0.2
                    - means.mean(axis=1, keepdims=True) * 0.2
                )

                alt_score = abs((means * checker_mask).mean())
                neighbor_score = (
                    np.abs(np.diff(means, axis=0)).mean()
                    + np.abs(np.diff(means, axis=1)).mean()
                ) * 0.5

                border_penalty = 0.0
                if x < 6 or y < 6 or x + side > w - 6 or y + side > h - 6:
                    border_penalty = 5.0

                score = (0.8 * alt_score) + (1.2 * neighbor_score) - border_penalty
                if best is None or score > best[0]:
                    best = (score, x, y, side)

    if best is None:
        return image

    _, x, y, side = best

    # Expand slightly so board borders are not clipped.
    pad = int(side * 0.06)
    x1 = max(0, x - pad)
    y1 = max(0, y - pad)
    x2 = min(w, x + side + pad)
    y2 = min(h, y + side + pad)

    cropped = image[y1:y2, x1:x2]
    if cropped.size == 0:
        return image

    # Final trim by edge energy to remove remaining floor/cloth margins.
    gray_crop = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
    gray_crop = cv2.GaussianBlur(gray_crop, (3, 3), 0)

    grad_x = np.abs(cv2.Sobel(gray_crop, cv2.CV_32F, 1, 0, ksize=3))
    grad_y = np.abs(cv2.Sobel(gray_crop, cv2.CV_32F, 0, 1, ksize=3))
    edge_mag = (grad_x + grad_y) * 0.5

    row_energy = edge_mag.mean(axis=1)
    col_energy = edge_mag.mean(axis=0)

    smooth_k = max(11, ((min(cropped.shape[0], cropped.shape[1]) // 12) | 1))
    smooth_kernel = cv2.getGaussianKernel(smooth_k, 0).ravel()

    row_energy = np.convolve(row_energy, smooth_kernel, mode="same")
    col_energy = np.convolve(col_energy, smooth_kernel, mode="same")

    row_thr = row_energy.mean() * 0.9
    col_thr = col_energy.mean() * 0.9

    ys = np.where(row_energy > row_thr)[0]
    xs = np.where(col_energy > col_thr)[0]

    if len(xs) == 0 or len(ys) == 0:
        return cropped

    tx1 = max(0, int(xs.min()) - 2)
    ty1 = max(0, int(ys.min()) - 2)
    tx2 = min(cropped.shape[1], int(xs.max()) + 3)
    ty2 = min(cropped.shape[0], int(ys.max()) + 3)

    # Keep only valid trims (avoid over-cropping on noisy frames).
    if (tx2 - tx1) < 0.6 * cropped.shape[1] or (ty2 - ty1) < 0.6 * cropped.shape[0]:
        return cropped

    trimmed = cropped[ty1:ty2, tx1:tx2]
    return trimmed if trimmed.size > 0 else cropped


def _build_edge_maps(gray):
    """
    Create multiple edge maps so contour detection is robust across lighting/camera noise.
    """
    maps = []
    for k in (5, 9, 13):
        blur = cv2.GaussianBlur(gray, (k, k), 0)
        maps.append(cv2.Canny(blur, 40, 140))
        maps.append(cv2.Canny(blur, 25, 100))

        adaptive = cv2.adaptiveThreshold(
            blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 5
        )
        maps.append(cv2.Canny(adaptive, 30, 120))

    return maps


def _find_largest_quad_contour(edge_maps, image_shape):
    """
    Find largest valid 4-point contour from all edge maps.
    Returns points or None.
    """
    h, w = image_shape[:2]
    image_area = float(h * w)
    best_area = 0.0
    best_quad = None

    for edge in edge_maps:
        work = cv2.dilate(edge, np.ones((3, 3), np.uint8), iterations=1)
        work = cv2.erode(work, np.ones((3, 3), np.uint8), iterations=1)

        contours_info = cv2.findContours(work, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        contours = contours_info[0] if len(contours_info) == 2 else contours_info[1]

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < image_area * 0.08:
                continue

            perimeter = cv2.arcLength(cnt, True)
            if perimeter <= 0:
                continue

            approx = cv2.approxPolyDP(cnt, 0.02 * perimeter, True)
            if len(approx) != 4 or not cv2.isContourConvex(approx):
                continue

            pts = approx.reshape(4, 2).astype("float32")
            x_min, y_min = pts.min(axis=0)
            x_max, y_max = pts.max(axis=0)

            # Reject full-frame quads.
            if x_min <= 1 and y_min <= 1 and x_max >= w - 2 and y_max >= h - 2:
                continue

            if area > best_area:
                best_area = area
                best_quad = pts

    return best_quad


def _find_best_min_rect(edge_maps, image_shape):
    """
    Fallback when no clean 4-point contour exists.
    Uses minAreaRect scored by size, shape, and border-touch penalties.
    """
    h, w = image_shape[:2]
    image_area = float(h * w)
    best_score = -1e9
    best_pts = None

    for edge in edge_maps:
        work = cv2.dilate(edge, np.ones((3, 3), np.uint8), iterations=1)
        work = cv2.erode(work, np.ones((3, 3), np.uint8), iterations=1)

        contours_info = cv2.findContours(work, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        contours = contours_info[0] if len(contours_info) == 2 else contours_info[1]

        for cnt in contours:
            contour_area = cv2.contourArea(cnt)
            if contour_area < image_area * 0.04:
                continue

            rect = cv2.minAreaRect(cnt)
            pts = cv2.boxPoints(rect).astype("float32")

            x_min, y_min = pts.min(axis=0)
            x_max, y_max = pts.max(axis=0)

            bw = max(1.0, float(x_max - x_min))
            bh = max(1.0, float(y_max - y_min))
            box_area = bw * bh
            area_ratio = box_area / image_area

            if area_ratio < 0.08 or area_ratio > 0.96:
                continue

            # Penalize contours that stick to many image edges.
            margin = 4
            edge_touch = 0
            if x_min <= margin:
                edge_touch += 1
            if y_min <= margin:
                edge_touch += 1
            if x_max >= w - 1 - margin:
                edge_touch += 1
            if y_max >= h - 1 - margin:
                edge_touch += 1

            aspect = max(bw, bh) / max(1.0, min(bw, bh))
            if aspect > 2.0:
                continue

            rectangularity = min(1.0, contour_area / max(1.0, box_area))

            # Score:
            # - prefer larger board-like rectangles
            # - penalize heavy border-touch and extreme aspect ratios
            score = 0.0
            score += area_ratio * 140.0
            score += rectangularity * 25.0
            score -= edge_touch * 12.0
            score -= abs(np.log(aspect)) * 18.0

            # Small center bias to avoid picking edge-only background regions.
            cx = (x_min + x_max) * 0.5
            cy = (y_min + y_max) * 0.5
            center_dist = ((cx - w * 0.5) ** 2 + (cy - h * 0.5) ** 2) ** 0.5
            score -= (center_dist / max(h, w)) * 6.0

            if score > best_score:
                best_score = score
                best_pts = pts

    return best_pts


def crop_chessboard(image):
    """
    Detect chessboard and return perspective-cropped board image.

    Primary path: detect the main board against the green background cloth.
    Main path: largest valid 4-point contour.
    Fallback: scored min-area rectangle when contour is fragmented.
    Returns None when no board-like region is found.
    """
    if image is None or image.size == 0:
        return None

    # Best path for this capture rig: the board is centered on green cloth.
    quad = _find_green_background_quad(image)
    if quad is not None:
        warped = _four_point_transform(image, quad)
        if warped is not None and warped.size > 0:
            return warped

    # Next best path for nearly top-down frames: recover the full board box from board lines.
    quad = _find_axis_aligned_board_box(image)
    if quad is not None:
        warped = _four_point_transform(image, quad)
        if warped is not None and warped.size > 0:
            return warped

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edge_maps = _build_edge_maps(gray)

    # Primary path: largest 4-point contour.
    quad = _find_largest_quad_contour(edge_maps, image.shape)
    if quad is not None:
        warped = _four_point_transform(image, quad)
        return _refine_checkerboard_region(warped)

    # Fallback path for difficult frames.
    quad = _find_best_min_rect(edge_maps, image.shape)
    if quad is not None:
        warped = _four_point_transform(image, quad)
        return _refine_checkerboard_region(warped)

    return None
