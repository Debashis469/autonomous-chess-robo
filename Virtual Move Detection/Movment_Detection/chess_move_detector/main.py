"""CLI entrypoint for chess move detection from before/after board images."""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2

from board_detection import align_board_to_reference, detect_and_crop_board
from config import (
    CHANGE_SCORE_RELATIVE_MIN,
    DEBUG,
    DEST_FILLING_DELTA_MIN,
    DIFF_THRESHOLD,
    MIN_CHANGE_AREA,
    MIN_MEAN_DIFF,
    OUTPUT_DIR,
    SOURCE_EMPTYING_DELTA_MIN,
    WARP_SIZE,
)
from game_state import (
    apply_move,
    get_piece_name,
    init_board,
    is_legal,
    load_board_state,
    save_board_state,
)
from move_finder import infer_move
from occupancy_detector import SquareChange, compute_score_grid, detect_changed_squares, estimate_occupancy
from square_extractor import split_into_squares
from utils import load_image, resize_keep_ratio
from visualizer import save_debug_images

DEFAULT_MOVE_OUTPUT_FILE = str(Path(__file__).resolve().parent.parent / "detected_move.txt")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Detect chess move from two board images.")
    parser.add_argument("--prev", required=True, help="Path to image before move.")
    parser.add_argument("--after", required=True, help="Path to image after move.")

    parser.add_argument("--warp-size", type=int, default=WARP_SIZE, help="Warped board size in pixels.")
    parser.add_argument("--diff-threshold", type=int, default=DIFF_THRESHOLD, help="Pixel diff threshold.")
    parser.add_argument(
        "--min-change-area",
        type=int,
        default=MIN_CHANGE_AREA,
        help="Minimum changed pixels in a square.",
    )
    parser.add_argument(
        "--min-mean-diff",
        type=float,
        default=MIN_MEAN_DIFF,
        help="Minimum mean absdiff in a square.",
    )
    parser.add_argument(
        "--relative-score-min",
        type=float,
        default=CHANGE_SCORE_RELATIVE_MIN,
        help="Keep only squares with score >= top_score * this value.",
    )
    parser.add_argument(
        "--source-emptying-delta-min",
        type=float,
        default=SOURCE_EMPTYING_DELTA_MIN,
        help="Minimum occupancy drop at source square to accept a move.",
    )
    parser.add_argument(
        "--dest-filling-delta-min",
        type=float,
        default=DEST_FILLING_DELTA_MIN,
        help="Minimum occupancy increase at destination square to accept a move.",
    )
    parser.add_argument(
        "--max-side",
        type=int,
        default=1600,
        help="Resize each input image so longest side is at most this value.",
    )
    parser.add_argument("--output-dir", default=OUTPUT_DIR, help="Directory for debug outputs.")
    parser.add_argument(
        "--state-file",
        default="board_state.fen",
        help="Path to persisted board state (FEN). Used to continue game across runs.",
    )
    parser.add_argument(
        "--reset-board",
        action="store_true",
        help="Ignore saved state and start from a fresh board for this run.",
    )
    parser.add_argument(
        "--fen",
        default=None,
        help="Optional starting FEN. If provided, it overrides saved state for this run.",
    )
    parser.add_argument(
        "--move-format",
        choices=("uci", "dash"),
        default="uci",
        help="Output style for detected move. 'uci' => e2e4, 'dash' => e2-e4.",
    )
    parser.add_argument(
        "--only-move",
        action="store_true",
        help="Print only the final move text (or <uncertain>).",
    )
    parser.add_argument(
        "--move-output-file",
        default=DEFAULT_MOVE_OUTPUT_FILE,
        help="Write final detected move text to this file (overwrites every run).",
    )

    parser.add_argument("--debug", dest="debug", action="store_true", help="Enable debug outputs.")
    parser.add_argument("--no-debug", dest="debug", action="store_false", help="Disable debug outputs.")
    parser.set_defaults(debug=DEBUG)
    return parser.parse_args()


def _format_move_text(move_uci: str, move_format: str) -> str:
    """Format UCI move text for requested output style."""
    if move_format == "dash" and len(move_uci) >= 4:
        return f"{move_uci[:2]}-{move_uci[2:4]}{move_uci[4:]}"
    return move_uci


def _write_move_output(path: str, move_text: str) -> Path:
    """Write detected move text to file, overwriting previous content."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(f"{move_text}\n", encoding="utf-8")
    return output_path


def _find_partner_square(
    known_square: SquareChange,
    prev_squares: list[list],
    after_squares: list[list],
    known_delta: float,
) -> SquareChange | None:
    """
    When only one changed square was detected, scan all 64 squares for the
    best occupancy partner: a square with opposite occupancy delta to the
    known square (source leaves -> find filler, or filler -> find source).
    """
    best_sq: SquareChange | None = None
    best_abs_delta = 0.0
    # If the known square barely changed in occupancy, we can't determine
    # direction reliably — scan for the largest absolute shift on any other square.
    sign_known = 1.0 if known_delta >= 0 else -1.0
    require_sign = abs(known_delta) >= 1.5  # only enforce opposite direction if signal is clear

    board_size = len(prev_squares)
    for row in range(board_size):
        for col in range(board_size):
            if row == known_square.row and col == known_square.col:
                continue
            before_occ = estimate_occupancy(prev_squares[row][col])
            after_occ = estimate_occupancy(after_squares[row][col])
            delta = after_occ - before_occ
            abs_delta = abs(delta)
            # When the known square's direction is clear, only look at the opposite direction.
            if require_sign and (delta * -sign_known) <= 0:
                continue
            if abs_delta > best_abs_delta:
                best_abs_delta = abs_delta
                best_sq = SquareChange(
                    row=row,
                    col=col,
                    changed_pixels=0,
                    changed_ratio=0.0,
                    mean_diff=0.0,
                    score=abs_delta,
                )

    # Only return if the partner has a meaningful occupancy shift
    if best_sq is not None and best_abs_delta >= 1.5:
        return best_sq
    return None


def run(args: argparse.Namespace) -> int:
    debug_enabled = args.debug and not args.only_move
    if args.fen:
        board = init_board(args.fen)
        board_state_loaded = True
    elif args.reset_board:
        board = init_board()
        board_state_loaded = False
    else:
        board, board_state_loaded = load_board_state(args.state_file)

    prev_img = resize_keep_ratio(load_image(args.prev), max_side=args.max_side)
    after_img = resize_keep_ratio(load_image(args.after), max_side=args.max_side)

    if prev_img.shape[:2] != after_img.shape[:2]:
        after_img = cv2.resize(
            after_img,
            (prev_img.shape[1], prev_img.shape[0]),
            interpolation=cv2.INTER_AREA,
        )
        if not args.only_move:
            print("Resized after image to match prev dimensions.")

    prev_board = detect_and_crop_board(
        prev_img,
        size=args.warp_size,
        debug=debug_enabled,
        output_dir=args.output_dir,
        debug_prefix="prev_",
    )
    after_board = detect_and_crop_board(
        after_img,
        size=args.warp_size,
        debug=debug_enabled,
        output_dir=args.output_dir,
    )
    after_board, align_ok = align_board_to_reference(prev_board, after_board)

    prev_squares = split_into_squares(prev_board)
    after_squares = split_into_squares(after_board)

    changed_squares = detect_changed_squares(
        prev_squares=prev_squares,
        after_squares=after_squares,
        diff_threshold=args.diff_threshold,
        min_change_area=args.min_change_area,
        min_mean_diff=args.min_mean_diff,
        relative_score_min=args.relative_score_min,
    )

    move = infer_move(
        changed_squares=changed_squares,
        prev_squares=prev_squares,
        after_squares=after_squares,
        source_emptying_delta_min=args.source_emptying_delta_min,
        dest_filling_delta_min=args.dest_filling_delta_min,
    )

    # Recovery: if inference failed and only 1 square was detected, search
    # all 64 squares for the best occupancy-delta partner and retry.
    # We use relaxed thresholds here because pixel-diff already confirmed a real
    # change on the known square — we just need to find its pair.
    if not move.move_uci and len(changed_squares) == 1:
        known_sq = changed_squares[0]
        before_occ = estimate_occupancy(prev_squares[known_sq.row][known_sq.col])
        after_occ = estimate_occupancy(after_squares[known_sq.row][known_sq.col])
        known_delta = after_occ - before_occ
        partner = _find_partner_square(known_sq, prev_squares, after_squares, known_delta)
        if partner is not None:
            augmented_squares = [known_sq, partner]
            # Use relaxed thresholds: pixel-diff already confirmed a real change
            RELAXED_DELTA = 1.5
            move = infer_move(
                changed_squares=augmented_squares,
                prev_squares=prev_squares,
                after_squares=after_squares,
                source_emptying_delta_min=RELAXED_DELTA,
                dest_filling_delta_min=RELAXED_DELTA,
            )
            if move.move_uci:
                changed_squares = augmented_squares

    changed_labels = ", ".join(item.algebraic for item in changed_squares)
    if debug_enabled:
        print(f"ECC alignment: {'ok' if align_ok else 'skipped'}")
        if args.fen:
            print("Board state source: --fen input")
        elif args.reset_board:
            print("Board state source: reset to default start")
        else:
            print(
                "Board state source: "
                + ("loaded from state file" if board_state_loaded else "default start position")
            )

    if move.move_uci:
        formatted_move = _format_move_text(move.move_uci, args.move_format)
    elif changed_labels:
        formatted_move = f"Changed: {changed_labels}"
    else:
        formatted_move = "Same"
    move_output_path = _write_move_output(args.move_output_file, formatted_move)
    moved_piece_name: str | None = None
    illegal_move_text: str | None = None
    source_piece_missing = False
    move_applied = False

    if move.move_uci:
        if is_legal(board, move.move_uci):
            moved_piece_name = get_piece_name(board, move.move_uci)
            if moved_piece_name is None:
                source_piece_missing = True
            else:
                move_applied = apply_move(board, move.move_uci)
                if move_applied:
                    save_board_state(board, args.state_file)
        else:
            illegal_move_text = move.move_uci

    if args.only_move:
        print(formatted_move)
    else:
        print(f"Detected changed squares: {changed_labels if changed_labels else 'none'}")
        print(f"Detected move: {formatted_move}")
        if illegal_move_text:
            print(f"Illegal move detected: {illegal_move_text}")
        elif source_piece_missing:
            print("No piece found on source square.")
        elif moved_piece_name:
            print(f"Moved piece: {moved_piece_name}")
            if move_applied and debug_enabled:
                print(f"Board state updated: {Path(args.state_file)}")
        print(f"Confidence: {move.confidence:.2f}")
        print(f"Move saved to: {move_output_path}")
        if move.warning:
            print(f"Warning: {move.warning}")

    if debug_enabled:
        score_grid = compute_score_grid(
            prev_squares=prev_squares,
            after_squares=after_squares,
            diff_threshold=args.diff_threshold,
        )
        saved = save_debug_images(
            output_dir=args.output_dir,
            prev_board=prev_board,
            after_board=after_board,
            changed_squares=changed_squares,
            score_grid=score_grid,
        )
        print(f"Debug outputs saved to: {Path(args.output_dir).resolve()}")
        for key, value in saved.items():
            print(f"  - {key}: {value}")

    # Exit code 0 = confident move, 2 = changed squares only / same board
    return 0 if move.move_uci else 2


def main() -> int:
    args = parse_args()
    try:
        return run(args)
    except Exception as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
