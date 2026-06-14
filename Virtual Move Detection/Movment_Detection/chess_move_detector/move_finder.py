"""Infer the most likely chess move from changed board squares."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from config import DEST_FILLING_DELTA_MIN, SOURCE_EMPTYING_DELTA_MIN
from occupancy_detector import SquareChange, estimate_occupancy


CASTLING_PATTERNS: dict[frozenset[str], str] = {
    frozenset(("e1", "g1", "h1", "f1")): "e1g1",  # white king-side
    frozenset(("e1", "c1", "a1", "d1")): "e1c1",  # white queen-side
    frozenset(("e8", "g8", "h8", "f8")): "e8g8",  # black king-side
    frozenset(("e8", "c8", "a8", "d8")): "e8c8",  # black queen-side
}


@dataclass(frozen=True)
class MoveInference:
    """Output object from move inference."""

    move_uci: str | None
    source_square: str | None
    destination_square: str | None
    changed_squares: list[str]
    confidence: float
    warning: str | None = None


def _detect_castling(changed_square_names: Sequence[str]) -> str | None:
    changed_set = frozenset(changed_square_names)
    for pattern, move in CASTLING_PATTERNS.items():
        if pattern.issubset(changed_set):
            return move
    return None


def infer_move(
    changed_squares: Sequence[SquareChange],
    prev_squares: list[list[np.ndarray]],
    after_squares: list[list[np.ndarray]],
    source_emptying_delta_min: float = SOURCE_EMPTYING_DELTA_MIN,
    dest_filling_delta_min: float = DEST_FILLING_DELTA_MIN,
) -> MoveInference:
    """
    Infer source and destination squares from changed squares.

    Typical move:
      - source square becomes emptier
      - destination square becomes fuller
    """
    if not changed_squares:
        return MoveInference(
            move_uci=None,
            source_square=None,
            destination_square=None,
            changed_squares=[],
            confidence=0.0,
            warning="No changed squares detected.",
        )

    changed_names = [change.algebraic for change in changed_squares]

    castling_move = _detect_castling(changed_names)
    if castling_move:
        return MoveInference(
            move_uci=castling_move,
            source_square=castling_move[:2],
            destination_square=castling_move[2:4],
            changed_squares=changed_names,
            confidence=0.95,
            warning=None,
        )

    occupancy_deltas: list[tuple[SquareChange, float]] = []
    for change in changed_squares:
        before_occ = estimate_occupancy(prev_squares[change.row][change.col])
        after_occ = estimate_occupancy(after_squares[change.row][change.col])
        occupancy_deltas.append((change, after_occ - before_occ))

    # Source tends to have the strongest negative occupancy delta.
    occupancy_deltas.sort(key=lambda item: item[1])
    source_change, source_delta = occupancy_deltas[0]
    source_square = source_change.algebraic

    if source_delta > -abs(source_emptying_delta_min):
        return MoveInference(
            move_uci=None,
            source_square=source_square,
            destination_square=None,
            changed_squares=changed_names,
            confidence=0.15,
            warning=(
                "No clear source-emptying signal. Likely small in-square motion/noise "
                "instead of a full square-to-square move."
            ),
        )

    # Destination tends to have a positive occupancy delta.
    destination_change: SquareChange | None = None
    positive_candidates = [
        item for item in occupancy_deltas[1:] if item[1] >= abs(dest_filling_delta_min)
    ]
    if positive_candidates:
        destination_change = max(positive_candidates, key=lambda item: item[1])[0]

    if destination_change is None:
        return MoveInference(
            move_uci=None,
            source_square=source_square,
            destination_square=None,
            changed_squares=changed_names,
            confidence=0.2,
            warning=(
                "No clear destination-filling signal. Likely small in-square motion/noise "
                "instead of a full square-to-square move."
            ),
        )

    destination_square = destination_change.algebraic
    if source_square == destination_square:
        return MoveInference(
            move_uci=None,
            source_square=source_square,
            destination_square=destination_square,
            changed_squares=changed_names,
            confidence=0.1,
            warning="Source and destination collapsed to same square.",
        )

    warning: str | None = None
    confidence = 0.9 if len(changed_squares) == 2 else 0.65

    if len(changed_squares) > 2:
        warning = "More than two squares changed; returning best-guess move."

    return MoveInference(
        move_uci=f"{source_square}{destination_square}",
        source_square=source_square,
        destination_square=destination_square,
        changed_squares=changed_names,
        confidence=float(np.clip(confidence, 0.0, 1.0)),
        warning=warning,
    )
