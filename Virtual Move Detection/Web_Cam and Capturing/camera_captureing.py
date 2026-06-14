import os
import shutil
import subprocess
import sys

import cv2
import numpy as np

from cropped_capture import crop_chessboard

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Output folders.
CROPPED_OUTPUT_DIR = os.path.join(SCRIPT_DIR, "cropped_image")
RAW_OUTPUT_DIR = os.path.join(SCRIPT_DIR, "raw_image")

# Movment_Detection integration.
PLACE_RECOG_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "Movment_Detection"))
MOVE_DETECTOR_DIR = os.path.join(PLACE_RECOG_ROOT, "chess_move_detector")
MOVE_OUTPUT_FILE = os.path.join(PLACE_RECOG_ROOT, "detected_move.txt")
MOVE_STATE_FILE = os.path.join(MOVE_DETECTOR_DIR, "board_state.fen")
MOVE_TMP_DIR = os.path.join(MOVE_DETECTOR_DIR, "tmp_move")
MOVE_TMP_PREV = os.path.join(MOVE_TMP_DIR, "prev.jpg")
MOVE_TMP_AFTER = os.path.join(MOVE_TMP_DIR, "after.jpg")
START_BOARD_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

# Motion detection settings.
MOTION_PIXEL_DIFF_THRESHOLD = 18
MOTION_REGION_RATIO = 0.003
MOTION_TOTAL_RATIO = 0.001
REFERENCE_PIXEL_DIFF_THRESHOLD = 12
REFERENCE_PIXEL_RATIO = 0.00045

# Stability settings.
STABLE_FRAME_COUNT = 20
STABLE_PIXEL_DIFF_THRESHOLD = 10
STABLE_PIXEL_RATIO = 0.003


def parse_camera_source():
    """
    Parse camera source from command line.
    Examples:
    - python camera_captureing.py
    - python camera_captureing.py 1
    - python camera_captureing.py http://192.168.1.4:4747/video
    """
    if len(sys.argv) < 2:
        return 0

    raw = sys.argv[1].strip()
    return int(raw) if raw.isdigit() else raw


def open_camera(source):
    """Open the requested camera source and try simple index fallbacks."""
    cap = cv2.VideoCapture(source)
    if cap.isOpened():
        return cap, source

    # If numeric source fails, try a few nearby indexes.
    if isinstance(source, int):
        cap.release()
        for alt in (1, 0, 2):
            if alt == source:
                continue
            alt_cap = cv2.VideoCapture(alt)
            if alt_cap.isOpened():
                print(f"[INFO] Camera {source} unavailable. Using camera index {alt}.")
                return alt_cap, alt
            alt_cap.release()

    return None, source


def build_output_path(output_dir, stem):
    """Create a safe output filename without overwriting existing images."""
    candidate = os.path.join(output_dir, f"{stem}.jpg")
    if not os.path.exists(candidate):
        return candidate

    suffix = 1
    while True:
        candidate = os.path.join(output_dir, f"{stem}_{suffix}.jpg")
        if not os.path.exists(candidate):
            return candidate
        suffix += 1


def _write_text_file(path, text):
    """Write UTF-8 text, creating parent folders when needed."""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


def reset_place_recog_session():
    """
    Reset move output and board state for a fresh game session.
    Assumes the first captured board image is the starting position.
    """
    if not os.path.isdir(MOVE_DETECTOR_DIR):
        print(f"[WARN] Movment_Detection detector folder not found: {MOVE_DETECTOR_DIR}")
        return False

    os.makedirs(MOVE_TMP_DIR, exist_ok=True)
    _write_text_file(MOVE_OUTPUT_FILE, "")
    _write_text_file(MOVE_STATE_FILE, f"{START_BOARD_FEN}\n")

    for temp_path in (MOVE_TMP_PREV, MOVE_TMP_AFTER):
        if os.path.exists(temp_path):
            os.remove(temp_path)

    print(f"[INFO] Reset Movment_Detection session: {MOVE_STATE_FILE}")
    return True


def detect_move_with_place_recog(prev_cropped_path, curr_cropped_path):
    """
    Send two cropped board images to Movment_Detection and return the detected move text.
    Returns (move_text, error_message).
    """
    if not os.path.isdir(MOVE_DETECTOR_DIR):
        return "<uncertain>", f"Movment_Detection detector folder not found: {MOVE_DETECTOR_DIR}"

    if not os.path.exists(prev_cropped_path):
        return "<uncertain>", f"Previous cropped image not found: {prev_cropped_path}"
    if not os.path.exists(curr_cropped_path):
        return "<uncertain>", f"Current cropped image not found: {curr_cropped_path}"

    os.makedirs(MOVE_TMP_DIR, exist_ok=True)
    shutil.copy2(prev_cropped_path, MOVE_TMP_PREV)
    shutil.copy2(curr_cropped_path, MOVE_TMP_AFTER)

    # Clear stale result so every run reflects the newest comparison.
    _write_text_file(MOVE_OUTPUT_FILE, "")

    command = [
        sys.executable,
        "main.py",
        "--prev",
        MOVE_TMP_PREV,
        "--after",
        MOVE_TMP_AFTER,
        "--no-debug",
        "--only-move",
        "--move-output-file",
        MOVE_OUTPUT_FILE,
        "--state-file",
        MOVE_STATE_FILE,
    ]

    try:
        completed = subprocess.run(
            command,
            cwd=MOVE_DETECTOR_DIR,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        _write_text_file(MOVE_OUTPUT_FILE, "Same\n")
        return "Same", "Movment_Detection timed out after 60 seconds."

    move_text = ""
    if os.path.exists(MOVE_OUTPUT_FILE):
        with open(MOVE_OUTPUT_FILE, "r", encoding="utf-8") as handle:
            move_text = handle.read().strip()

    stdout_lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    stderr_lines = [line.strip() for line in completed.stderr.splitlines() if line.strip()]

    if not move_text and stdout_lines:
        move_text = stdout_lines[-1]
    if not move_text:
        move_text = "Same"
        _write_text_file(MOVE_OUTPUT_FILE, f"{move_text}\n")

    if completed.returncode not in (0, 2):
        details = " | ".join(stdout_lines + stderr_lines)
        if not details:
            details = f"Movment_Detection returned exit code {completed.returncode}."
        return move_text, details

    return move_text, None


def save_frame_pair(cropped_output_dir, raw_output_dir, frame, names):
    """
    Save both cropped and raw versions for one or more logical names.
    Returns (saved_records, error_message).
    """
    os.makedirs(cropped_output_dir, exist_ok=True)
    os.makedirs(raw_output_dir, exist_ok=True)

    cropped = crop_chessboard(frame)
    if cropped is None:
        return [], "Board contour was not detected."

    saved_records = []
    for name in names:
        cropped_filename = build_output_path(cropped_output_dir, name)
        raw_filename = build_output_path(raw_output_dir, name)

        if not cv2.imwrite(cropped_filename, cropped):
            return saved_records, f"Failed to save {cropped_filename}."
        if not cv2.imwrite(raw_filename, frame):
            return saved_records, f"Failed to save {raw_filename}."

        saved_records.append(
            {
                "name": name,
                "cropped": cropped_filename,
                "raw": raw_filename,
            }
        )

    return saved_records, None


def _build_motion_mask(base_gray, curr_gray, pixel_threshold):
    """Create a denoised binary motion mask between two grayscale frames."""
    diff = cv2.absdiff(base_gray, curr_gray)
    _, motion_mask = cv2.threshold(diff, pixel_threshold, 255, cv2.THRESH_BINARY)
    motion_mask = cv2.medianBlur(motion_mask, 5)
    motion_mask = cv2.dilate(motion_mask, None, iterations=2)
    return motion_mask


def detect_motion(prev_gray, curr_gray, reference_gray=None):
    """
    Detect both active motion and cumulative board change.
    Returns (transient_motion, board_changed, motion_mask).
    """
    motion_mask = _build_motion_mask(prev_gray, curr_gray, MOTION_PIXEL_DIFF_THRESHOLD)

    h, w = motion_mask.shape
    h2, w2 = h // 2, w // 2

    regions = [
        motion_mask[0:h2, 0:w2],
        motion_mask[0:h2, w2:w],
        motion_mask[h2:h, 0:w2],
        motion_mask[h2:h, w2:w],
    ]

    region_area = max(1, h2 * w2)
    total_area = max(1, h * w)
    region_limit = max(250, int(region_area * MOTION_REGION_RATIO))
    total_limit = max(450, int(total_area * MOTION_TOTAL_RATIO))

    transient_motion = False
    for region in regions:
        if cv2.countNonZero(region) > region_limit:
            transient_motion = True
            break

    if not transient_motion and cv2.countNonZero(motion_mask) > total_limit:
        transient_motion = True

    board_changed = False
    if reference_gray is not None:
        reference_mask = _build_motion_mask(reference_gray, curr_gray, REFERENCE_PIXEL_DIFF_THRESHOLD)
        reference_limit = max(300, int(total_area * REFERENCE_PIXEL_RATIO))
        board_changed = cv2.countNonZero(reference_mask) > reference_limit
        motion_mask = cv2.max(motion_mask, reference_mask)

    return transient_motion, board_changed, motion_mask


def check_stability(stable_ref_gray, curr_gray):
    """Compare two stable candidates and return whether scene change is very small."""
    diff = cv2.absdiff(stable_ref_gray, curr_gray)
    _, stable_mask = cv2.threshold(diff, STABLE_PIXEL_DIFF_THRESHOLD, 255, cv2.THRESH_BINARY)

    changed_pixels = cv2.countNonZero(stable_mask)
    total_pixels = stable_mask.shape[0] * stable_mask.shape[1]
    pixel_limit = max(250, int(total_pixels * STABLE_PIXEL_RATIO))

    return changed_pixels <= pixel_limit, stable_mask, changed_pixels, pixel_limit


def main():
    os.makedirs(CROPPED_OUTPUT_DIR, exist_ok=True)
    os.makedirs(RAW_OUTPUT_DIR, exist_ok=True)

    camera_source = parse_camera_source()
    cap, active_source = open_camera(camera_source)

    if cap is None:
        print("[ERROR] Camera could not be opened.")
        print("Try: python camera_captureing.py 0")
        print("Or : python camera_captureing.py http://<droidcam-ip>:4747/video")
        return

    print(f"[INFO] Using camera source: {active_source}")

    ok, first_frame = cap.read()
    if not ok or first_frame is None:
        print("[ERROR] Camera opened but no frames were received.")
        cap.release()
        return

    prev_gray = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)
    prev_gray = cv2.GaussianBlur(prev_gray, (5, 5), 0)

    capture_index = 1
    initial_capture_pending = True
    motion_detected = False
    stable_frames = 0
    stable_reference = None
    board_reference_gray = prev_gray.copy()
    previous_capture_record = None
    stable_mask_display = np.zeros_like(prev_gray)

    while True:
        ok, frame = cap.read()
        if not ok or frame is None:
            print("[WARN] Failed to read frame from camera. Stopping.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)

        status_text = "Watching board"
        status_color = (0, 255, 0)

        if initial_capture_pending:
            saved_records, error_message = save_frame_pair(
                CROPPED_OUTPUT_DIR, RAW_OUTPUT_DIR, frame, [str(capture_index)]
            )

            if error_message is None:
                record = saved_records[0]
                print(f"[INFO] Saved cropped: {record['cropped']}")
                print(f"[INFO] Saved raw: {record['raw']}")
                initial_capture_pending = False
                board_reference_gray = gray.copy()
                previous_capture_record = record
                reset_place_recog_session()
                status_text = f"Saved {capture_index} - ready"
                status_color = (255, 255, 0)
                capture_index += 1
            else:
                status_text = f"Waiting to save {capture_index}"
                status_color = (0, 165, 255)

            prev_gray = gray
            preview = frame.copy()
            cv2.putText(preview, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
            cv2.putText(preview, "Press q to quit", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (210, 210, 210), 2)

            cv2.imshow("Live", preview)
            cv2.imshow("Motion Mask", np.zeros_like(gray))
            cv2.imshow("Stable Diff", stable_mask_display)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
            continue

        transient_motion, board_changed, motion_mask = detect_motion(
            prev_gray, gray, board_reference_gray
        )

        # 1) Register motion or board change event.
        if transient_motion or board_changed:
            motion_detected = True
            if transient_motion:
                stable_frames = 0
                stable_reference = None

        # 2) Once movement stops, count stable frames.
        if not transient_motion and motion_detected:
            if stable_reference is None:
                stable_reference = gray.copy()
                stable_frames = 1
            else:
                stable_frames += 1

        if transient_motion:
            status_text = "Motion detected - waiting for stop"
            status_color = (0, 0, 255)
        elif motion_detected:
            status_text = f"Checking stable frames: {stable_frames}/{STABLE_FRAME_COUNT}"
            status_color = (0, 255, 255)

        # 3) Capture only if we had motion and scene stayed stable.
        if motion_detected and stable_reference is not None and stable_frames >= STABLE_FRAME_COUNT:
            stable_ok, stable_mask, changed_pixels, pixel_limit = check_stability(stable_reference, gray)
            stable_mask_display = stable_mask

            if stable_ok:
                names = [str(capture_index)]
                saved_records, error_message = save_frame_pair(
                    CROPPED_OUTPUT_DIR, RAW_OUTPUT_DIR, frame, names
                )

                if error_message is None:
                    current_record = saved_records[0]
                    print(f"[INFO] Saved cropped: {current_record['cropped']}")
                    print(f"[INFO] Saved raw: {current_record['raw']}")

                    move_text = ""
                    move_error = None
                    if previous_capture_record is not None:
                        move_text, move_error = detect_move_with_place_recog(
                            previous_capture_record["cropped"],
                            current_record["cropped"],
                        )
                        if move_error is None:
                            print(f"[INFO] Detected move: {move_text}")
                        else:
                            print(f"[WARN] Move detection issue: {move_error}")

                    if move_text:
                        status_text = f"Saved {capture_index} | Move {move_text}"
                    else:
                        status_text = f"Saved {capture_index}"
                    status_color = (255, 255, 0) if move_error is None else (0, 165, 255)

                    board_reference_gray = gray.copy()
                    previous_capture_record = current_record
                    capture_index += 1
                else:
                    print(f"[WARN] Stable frame found, but {error_message}")

                # Reset pipeline for the next capture attempt.
                motion_detected = False
                stable_frames = 0
                stable_reference = None
            else:
                # Scene still changing. Restart stable window.
                stable_reference = gray.copy()
                stable_frames = 1
                status_text = f"Not stable yet: {changed_pixels}/{pixel_limit}"
                status_color = (0, 165, 255)
        else:
            stable_mask_display = np.zeros_like(gray)

        prev_gray = gray

        preview = frame.copy()
        cv2.putText(preview, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        cv2.putText(preview, "Press q to quit", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (210, 210, 210), 2)

        cv2.imshow("Live", preview)
        cv2.imshow("Motion Mask", motion_mask)
        cv2.imshow("Stable Diff", stable_mask_display)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
