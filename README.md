# ♕ Autonomous Chess Robot ♕

An advanced chess-playing robot system that combines artificial intelligence, robotics, and computer vision to play chess autonomously. The system detects board state changes through computer vision, evaluates positions using a dedicated chess engine, controls a robotic arm to make moves, and communicates with human players.



![ARM Chess Robot](assets/robo.gif)


## Overview

This project implements a complete autonomous chess system with the following capabilities:

- **AI Chess Engine**: Minimax-based evaluation and move searching with piece-specific evaluation heuristics
- **Physical Robot Control**: Complete kinematic and motion control for a robotic arm performing chess moves
- **Computer Vision**: Real-time board detection and move recognition from camera feeds
- **Game Management**: Full chess game orchestration with human-robot interaction

## Key Features

✅ **Full Chess Engine**
- Legal move generation with bitboard representation
- Piece evaluation (pawns, knights, bishops, rooks, queens, kings)
- Minimax search with configurable depth
- FEN (Forsyth-Edwards Notation) support for game state representation

✅ **Robot Arm Control**
- Forward and inverse kinematics calculations
- Gripper control for piece manipulation
- Trajectory planning and motion primitives
- Serial communication with hardware

✅ **Computer Vision**
- Chess board detection and localization
- Square occupancy detection
- Move detection by comparing board states
- Multi-image processing pipeline

✅ **Game Logic**
- Complete chess game orchestration
- Turn management (human vs. robot)
- Move validation and legality checking
- Game state persistence

## System Architecture

```
┌─────────────────────────────────────────────────┐
│            Game Controller                       │
│  (Orchestrates human-robot gameplay)            │
└──────┬──────────────────────────┬───────────────┘
       │                          │
       ▼                          ▼
┌──────────────────┐    ┌─────────────────────┐
│  Chess Engine    │    │  Robot Control      │
│                  │    │                     │
│ - Move Gen       │    │ - Kinematics        │
│ - Evaluation     │    │ - Motion Primitives │
│ - Search (AI)    │    │ - Gripper Control   │
│ - FEN Support    │    │ - Serial Comm       │
└──────────────────┘    └─────────────────────┘
       ▲                          ▲
       │                          │
       └──────────────┬───────────┘
                      │
                      ▼
         ┌────────────────────────┐
         │  Vision Pipeline       │
         │                        │
         │ - Board Detection      │
         │ - Occupancy Detection  │
         │ - Move Finding         │
         │ - Image Processing     │
         └────────────────────────┘
```

## Project Structure

### `/engine` - Chess Engine
The core chess logic and AI decision-making system.

- **`board/`**: Board representation and FEN conversion
  - `board.hpp`: Core board state and piece tracking
  - `fen.cpp/hpp`: FEN string parsing and generation
  - `board_to_fen.cpp/hpp`: Board-to-FEN conversion utilities

- **`eval/`**: Position evaluation and piece value calculation
  - `eval.cpp/hpp`: Overall position evaluation
  - `pieces/`: Individual piece evaluation (pawn, knight, bishop, rook, queen, king)
  - `utils/`: Bitboard utilities and chess constants

- **`move/`**: Move representation and execution
  - `move.cpp/hpp`: Move data structures
  - `makemove.cpp/hpp`: Move application and board updates

- **`movegen/`**: Legal move generation
  - `movegen.cpp/hpp`: Pseudo-legal move generation
  - `legal.cpp/hpp`: Legal move filtering and validation

- **`search/`**: Game tree search algorithms
  - `search.cpp/hpp`: Minimax search with configurable depth

- **`utils/`**: Helper utilities
  - `move_to_string.cpp/hpp`: Move notation conversion
  - `types.hpp`: Shared type definitions

### `/game` - Game Management
Orchestrates gameplay between human and robot players.

- `game.cpp/hpp`: Main game loop and state management
- `chess_interface.cpp/hpp`: Chess rules enforcement
- `robot_interface.cpp/hpp`: Robot communication layer

### `/robo` - Robot Control
Complete robotic arm control system.

- **`config/`**: Robot configuration
  - `robo_params.hpp`: Kinematic parameters and hardware limits

- **`control/`**: Low-level hardware control
  - `serial_comm.cpp/hpp`: Serial communication protocol
  - `gripper.cpp/hpp`: End-effector control

- **`kinematics/`**: Motion mathematics
  - `ik.cpp/hpp`: Inverse kinematics calculations

- **`motion/`**: High-level motion control
  - `primitives.cpp/hpp`: Basic movement primitives (move, pick, place, throw)
  - `tasks.cpp/hpp`: Complex movement tasks

- **`robocontrol/`**: Motion orchestration
  - `robo_control.cpp/hpp`: Interface for all robot operations

- **`trajectory/`**: Path planning
  - `trajectory.cpp/hpp`: Trajectory generation and interpolation

- **`utils/`**: Robot utilities
  - `chess_map.cpp/hpp`: Chess square ↔ Cartesian coordinate mapping
  - `math_utils.cpp/hpp`: Mathematical helpers

### `/Virtual Move Detection` - Computer Vision
Board state detection and move inference.

- **`Movment_Detection/chess_move_detector/`**: Core move detection
  - `board_detection.py`: Detect and localize chess board in images
  - `occupancy_detector.py`: Detect which squares are occupied
  - `move_finder.py`: Compare board states to find moves
  - `game_state.py`: Track game state from FEN
  - `square_extractor.py`: Extract individual square images
  - `visualizer.py`: Visualization utilities
  - `main.py`: Main detection pipeline
  - `sample_data/`: Reference images for testing

- **`Web_Cam and Capturing/`**: Image acquisition
  - `camera_captureing.py`: Real-time camera capture
  - `cropped_capture.py`: Image cropping utilities
  - `rotate_crop_board.py`: Board rotation and cropping

- **`pipeline_main.py`**: End-to-end pipeline orchestration

## Requirements

### Hardware
- Robotic arm with forward/inverse kinematics compatibility
- Serial communication interface (USB/RS-485)
- Gripper/end-effector for piece handling
- USB camera for board state detection
- Chess board and pieces

### Software Dependencies

**C++ Components** (Chess Engine & Robot Control)
- C++11 or later
- Standard Library (iostream, string, vector, etc.)

**Python Components** (Computer Vision)
- Python 3.7+
- OpenCV (≥4.8.0)
- NumPy (≥1.24.0)
- python-chess (≥1.10.0)

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/Autonomous-Chess-Robot.git
cd Autonomous-Chess-Robot
```

### 2. Install Python Dependencies
```bash
cd "Virtual Move Detection"
pip install -r "Movment_Detection/chess_move_detector/requirements.txt"
```

### 3. Build C++ Components
```bash
# Build chess engine and game controller
cd /path/to/project
mkdir build
cd build
cmake ..
make

# Build robot control system
mkdir robo_build
cd robo_build
cmake ../robo
make
```

### 4. Hardware Configuration
- Update robot kinematic parameters in `robo/config/robo_params.hpp`
- Configure serial port settings in `robo/control/serial_comm.cpp`
- Calibrate camera and board detection parameters in `Virtual Move Detection/Movment_Detection/chess_move_detector/config.py`

## Usage

### Game Mode (Human vs. Robot)
```bash
./build/chess_game
```
Follow the prompts to:
1. Enter your chess moves in algebraic notation (e.g., e2e4)
2. Wait for the robot to calculate and execute its move
3. The vision system will detect your next move

**Game Flow:**
- Human makes a move (or detected by vision system)
- Robot calculates best move using chess engine (depth configurable)
- Robot physically executes the move
- Cycle repeats until checkmate or draw

### Robot Control Modes
```bash
./robo_build/robot_control
```
Menu options:
1. **IK Test Mode**: Test inverse kinematics calculations
2. **Pick Mode**: Pick a piece from a square
3. **Pick and Place**: Execute a complete move (e.g., e2e4)
4. **Pick and Throw**: Remove a captured piece
5. **Move to Rest**: Return arm to home position

### Vision System Only
```bash
cd "Virtual Move Detection/Movment_Detection/chess_move_detector"
python main.py --prev sample_data/prev.jpg --after sample_data/after.jpg
```

### End-to-End Pipeline
```bash
cd "Virtual Move Detection"
python pipeline_main.py
```

## Configuration

### Chess Engine Depth
Modify search depth in `game/game.cpp` to balance difficulty vs. response time:
```cpp
std::string bestMove = solveFen(fenString, 4);  // depth = 4
```
- Depth 3-4: Real-time play
- Depth 5-6: Stronger positions, longer computation
- Depth 7+: Very slow but near-optimal moves

### Robot Parameters
Edit `robo/config/robo_params.hpp`:
```cpp
// Arm length, joint limits, speed parameters
static constexpr double LINK1_LENGTH = 150.0;  // mm
static constexpr double LINK2_LENGTH = 150.0;  // mm
static constexpr double MAX_SPEED = 50.0;      // mm/s
```

### Vision Calibration
Edit `Virtual Move Detection/Movment_Detection/chess_move_detector/config.py`:
```python
BOARD_SIZE = 8  # Standard chess board
SQUARE_SIZE = 50  # pixels
PIECE_DETECTION_THRESHOLD = 0.5
```

## API Reference

### Chess Engine
```cpp
// Solve position and return best move
std::string solveFen(const std::string& fen, int depth);
```

### Robot Control
```cpp
bool runPickPlaceMode(const std::string& move);  // Execute move (e.g., "e2e4")
bool runPickMode(const std::string& sq);         // Pick from square
bool runPickThrowMode(const std::string& sq);    // Remove piece
bool runMoveMode(double x, double y, double z);  // Direct Cartesian movement
```

### Vision Pipeline
```python
from chess_move_detector.main import detect_move
move = detect_move('prev.jpg', 'after.jpg')  # Returns chess move notation
```

## Development Workflow

### Adding New Evaluation Heuristics
1. Create new file in `engine/eval/pieces/`
2. Implement piece evaluation function
3. Register in `engine/eval/eval.cpp`
4. Adjust weights in `engine/utils/constants.hpp`

### Adding Robot Primitives
1. Create function in `robo/motion/primitives.cpp`
2. Declare in `robo/motion/primitives.hpp`
3. Register in `robo/robocontrol/robo_control.cpp`
4. Add menu option in `robo/main.cpp`

### Improving Vision Detection
1. Add test images to `Virtual Move Detection/Movment_Detection/chess_move_detector/sample_data/`
2. Modify detection algorithms in:
   - `board_detection.py`: Board localization
   - `occupancy_detector.py`: Piece detection
   - `move_finder.py`: Move inference
3. Run `main.py` with `--debug` flag for visualization

## Testing

### Unit Tests
```bash
# Test individual components
./build/test_engine
./robo_build/test_robot
```

### Integration Tests
```bash
# Test complete game flow without robot
python test_game_simulation.py

# Test with physical robot (ensure safety)
./robo_build/robot_control
```

### Vision Testing
```bash
cd "Virtual Move Detection/Movment_Detection/chess_move_detector"
python main.py --prev sample_data/prev.jpg --after sample_data/after.jpg --debug
```

## Troubleshooting

### Robot Not Moving
- Check serial connection: `robo/control/serial_comm.cpp`
- Verify configuration in `robo/config/robo_params.hpp`
- Test with `IK Test Mode` first

### Vision Detection Failing
- Improve lighting conditions
- Recalibrate camera using `rotate_crop_board.py`
- Check image quality in `raw_image/` directory
- Adjust thresholds in `config.py`

### Chess Engine Slow
- Reduce search depth in `game/game.cpp`
- Enable alpha-beta pruning optimizations
- Use transposition tables (if implemented)

### Serial Communication Errors
- Verify COM port in `robo/control/serial_comm.cpp`
- Check baud rate: typically 115200
- Ensure robot firmware compatibility

## Performance Metrics

- **Chess Engine**: ~10,000-100,000 positions evaluated per move (depth-dependent)
- **Vision Detection**: ~500ms per board state analysis
- **Robot Move Execution**: 10-30 seconds per move (including gripper control)
- **Game Round Trip**: ~2-5 minutes (engine + robot execution + vision)

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/YourFeature`)
3. Commit your changes (`git commit -am 'Add YourFeature'`)
4. Push to the branch (`git push origin feature/YourFeature`)
5. Submit a pull request

### Areas for Contribution
- Enhanced evaluation functions for stronger play
- Multi-threading for faster search
- Advanced move ordering and pruning
- Improved vision algorithms (neural networks)
- Additional robot primitives
- Web interface for remote gameplay

## Known Limitations

- Single-threaded chess engine (could benefit from parallelization)
- Vision system assumes standard lighting conditions
- Robot arm limited to chess board workspace
- No endgame tablebases (would improve late-game play)
- FEN support without move history (chess960 not supported)


## Acknowledgments

- Chess rules and FEN implementation based on standard chess notation
- Robotic kinematics based on Denavit-Hartenberg conventions
- Computer vision techniques adapted from OpenCV documentation

---

**Last Updated**: May 2026
**Current Version**: 1.0.0
