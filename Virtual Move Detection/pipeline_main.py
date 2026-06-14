import os
import shutil
from glob import glob
import subprocess

# Paths
RAW_IMAGE_DIR = os.path.join('Web_Cam and Capturing', 'raw_image')
CROPPED_IMAGE_DIR = os.path.join('Web_Cam and Capturing', 'cropped_image')
SAMPLE_DATA_DIR = os.path.join('Movment_Detection', 'chess_move_detector', 'sample_data')
MOVE_DETECTOR_DIR = os.path.join('Movment_Detection', 'chess_move_detector')
DETECTED_MOVE_FILE = os.path.join('Movment_Detection', 'detected_move.txt')

# Step 1: Get latest two raw images
raw_images = sorted(glob(os.path.join(RAW_IMAGE_DIR, '*.jpg')), key=os.path.getmtime)
if len(raw_images) < 2:
    raise RuntimeError('Not enough raw images in raw_image folder.')
latest_two = raw_images[-2:]

# Step 2: Crop images and save to cropped_image
import sys
sys.path.append('Web_Cam and Capturing')
from cropped_capture import crop_chessboard
import cv2

cropped_paths = []
for idx, raw_path in enumerate(latest_two, 1):
    img = cv2.imread(raw_path)
    cropped = crop_chessboard(img)
    if cropped is None:
        raise RuntimeError(f'Could not crop image: {raw_path}')
    cropped_path = os.path.join(CROPPED_IMAGE_DIR, f'latest_{idx}.jpg')
    cv2.imwrite(cropped_path, cropped)
    cropped_paths.append(cropped_path)

# Step 3: Copy cropped images to sample_data as prev.jpg and after.jpg
prev_path = os.path.join(SAMPLE_DATA_DIR, 'prev.jpg')
after_path = os.path.join(SAMPLE_DATA_DIR, 'after.jpg')
shutil.copy2(cropped_paths[0], prev_path)
shutil.copy2(cropped_paths[1], after_path)

# Step 4: Run move detector
cmd = [
    'python', 'main.py',
    '--prev', 'sample_data/prev.jpg',
    '--after', 'sample_data/after.jpg',
    '--no-debug', '--only-move',
    '--move-output-file', '../../detected_move.txt'
]
subprocess.run(cmd, cwd=MOVE_DETECTOR_DIR, check=True)

print(f"Move written to {DETECTED_MOVE_FILE}")
