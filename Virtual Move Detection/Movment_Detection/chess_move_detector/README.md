# chess_move_detector

Classical computer-vision pipeline to detect a chess move from two board images:

- `prev.jpg` (before move)
- `after.jpg` (after move)

The program outputs a best-guess move in UCI format (for example `e2e4`, `g1f3`).

## Features

- Python 3.10+
- Uses only `opencv-python`, `numpy`, and standard library
- Modular, production-style structure
- Configurable thresholds
- Debug mode with saved visual artifacts
- Fallback behavior if board contour detection fails

## Project Structure

```text
chess_move_detector/
  main.py
  config.py
  board_detection.py
  square_extractor.py
  occupancy_detector.py
  move_finder.py
  utils.py
  visualizer.py
  requirements.txt
  README.md
  sample_data/
    prev.jpg
    after.jpg
```

## Installation

```bash
cd chess_move_detector
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python main.py --prev sample_data/prev.jpg --after sample_data/after.jpg
```

Debug mode is enabled by default (`DEBUG = True` in `config.py`).  
You can override behavior:

```bash
python main.py ^
  --prev sample_data/prev.jpg ^
  --after sample_data/after.jpg ^
  --debug ^
  --diff-threshold 30 ^
  --min-change-area 140 ^
  --min-mean-diff 8 ^
  --output-dir outputs
```

If you only want move text and no debug images:

```bash
python main.py --prev sample_data/prev.jpg --after sample_data/after.jpg --no-debug --only-move
```

For chess-style dash format:

```bash
python main.py --prev sample_data/prev.jpg --after sample_data/after.jpg --move-format dash --no-debug
```

For stability against tiny in-square piece jitter:

```bash
python main.py --prev sample_data/prev.jpg --after sample_data/after.jpg --no-debug ^
  --source-emptying-delta-min 8 ^
  --dest-filling-delta-min 8 ^
  --relative-score-min 0.62
```

## Example Output

```text
Detected changed squares: e2, e4
Detected move: e2e4
Confidence: 0.90
```

## How It Works

1. Load previous and current images.
2. Detect board corners (largest 4-point contour).
3. Perspective-warp board to top-down square (`WARP_SIZE x WARP_SIZE`).
4. Split into `8x8` squares.
5. Compare each matching square (grayscale absdiff + thresholded change area).
6. Rank changed squares.
7. Infer source/destination based on occupancy delta.
8. Output UCI move.
9. Save debug overlays + heatmap (if debug enabled).

## Assumptions

- Fixed camera setup
- Same board visible in both frames
- No hand or major occlusion during capture
- Reasonably stable lighting

## Limitations (v1)

- No piece classification model
- No full legal-move validation
- Promotion piece letter is not inferred yet (for example `e7e8q`)
- Sensitive to severe shadows/reflections

## Future Upgrades

- YOLO-based piece detection
- Full board-state tracking and move legality checks
- Promotion type prediction
- Better robustness for non-uniform lighting and slight camera shifts

## Config Tuning

Edit constants in `config.py` or override from CLI:

- `DIFF_THRESHOLD`: pixel-level change sensitivity
- `MIN_CHANGE_AREA`: minimum changed pixels in a square
- `MIN_MEAN_DIFF`: minimum mean intensity difference
- `WARP_SIZE`: board normalization size
- `--relative-score-min`: suppress weak/noisy changed squares
- `--source-emptying-delta-min`: reject moves where source does not clearly empty
- `--dest-filling-delta-min`: reject moves where destination does not clearly fill

## Output Files (Debug)

Saved under `outputs/`:

- `prev_warped.jpg`
- `after_warped.jpg`
- `prev_changed_overlay.jpg`
- `after_changed_overlay.jpg`
- `comparison_panel.jpg`
- `square_diff_heatmap.jpg`
- `after_heatmap_overlay.jpg`
