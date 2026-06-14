"""Global configuration values for the chess move detector."""

BOARD_SIZE = 8
WARP_SIZE = 800

# Pixel-level difference threshold used after absdiff on grayscale squares.
DIFF_THRESHOLD = 30

# Minimum number of changed pixels in a square to treat it as changed.
MIN_CHANGE_AREA = 140

# Minimum mean absolute difference for a square to be treated as changed.
MIN_MEAN_DIFF = 8.0

# Crop margin used for square comparison (ignores square borders where warp noise is highest).
SQUARE_INNER_CROP_RATIO = 0.12

# Keep only squares with score >= strongest_score * this factor.
CHANGE_SCORE_RELATIVE_MIN = 0.58

# Move inference thresholds (occupancy after-before deltas).
# Source must be <= -SOURCE_EMPTYING_DELTA_MIN.
SOURCE_EMPTYING_DELTA_MIN = 6.0
# Destination must be >= DEST_FILLING_DELTA_MIN.
DEST_FILLING_DELTA_MIN = 6.0

# Safety cap for noisy scenes.
MAX_CHANGED_SQUARES = 10

# Board detection tuning.
BOARD_CONTOUR_MIN_AREA_RATIO = 0.12
BLUR_KERNEL = 5
CANNY_LOW = 50
CANNY_HIGH = 150

DEBUG = True
OUTPUT_DIR = "outputs"
