#include "game.hpp"

#include <iostream>
#include <vector>

#include "../engine/board/board_to_fen.hpp"
#include "../engine/board/fen.hpp"
#include "../engine/move/makemove.hpp"
#include "../engine/movegen/legal.hpp"
#include "../engine/utils/move_to_string.hpp"
#include "chess_interface.hpp"
#include "robot_interface.hpp"

using namespace std;

Game::Game() : gameOver(false) {
    if (!parseFEN(
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            board)) {
        gameOver = true;
    }
}

Game::~Game() {
    robotShutdown();
}

bool Game::isValidMoveFormat(const string& move) {
    if (move.size() != 4) {
        return false;
    }

    char f1 = move[0];
    char r1 = move[1];
    char f2 = move[2];
    char r2 = move[3];

    bool sourceOk =
        (f1 >= 'a' && f1 <= 'h') &&
        (r1 >= '1' && r1 <= '8');

    bool destOk =
        (f2 >= 'a' && f2 <= 'h') &&
        (r2 >= '1' && r2 <= '8');

    return sourceOk && destOk;
}

bool Game::isLegalMove(const string& move) {
    vector<Move> legalMoves = generateLegalMoves(board);

    for (const Move& m : legalMoves) {
        if (moveToString(m) == move) {
            return true;
        }
    }

    return false;
}

bool Game::isCaptureMove(const string& move) {
    vector<Move> legalMoves = generateLegalMoves(board);

    for (const Move& m : legalMoves) {
        if (moveToString(m) == move) {
            return m.flag == CAPTURE;
        }
    }

    return false;
}

void Game::applyMove(const string& move) {
    vector<Move> legalMoves = generateLegalMoves(board);

    for (const Move& m : legalMoves) {
        if (moveToString(m) == move) {
            Undo u;
            makeMove(board, m, u);
            return;
        }
    }
}

void Game::printTurn() {
    cout << "\n=========================\n";

    if (board.whiteToMove) {
        cout << "WHITE TO MOVE\n";
    } else {
        cout << "BLACK TO MOVE\n";
    }

    cout << "=========================\n";
}

void Game::stopOnRobotFailure(const string& context) {
    cout << "\n[ROBOT] Failure during " << context << ". Stopping game to avoid desync.\n";
    gameOver = true;
}

void Game::handleHumanMove() {
    while (true) {
        string move;

        cout << "\nEnter move: ";
        cin >> move;

        if (!isValidMoveFormat(move)) {
            cout << "\nInvalid format\n";
            continue;
        }

        if (!isLegalMove(move)) {
            cout << "\nIllegal move\n";
            continue;
        }

        applyMove(move);

        cout << "\n[HUMAN] Played: " << move << "\n";
        break;
    }
}

void Game::handleRobotMove() {
    string fen = boardToFEN(board);

    cout << "\n[ENGINE] Thinking...\n";

    string engineMove = getEngineMove(fen);

    if (engineMove == "checkmate" ||
        engineMove == "stalemate" ||
        engineMove == "invalid") {
        cout << "\nGame Over: " << engineMove << "\n";
        gameOver = true;
        return;
    }

    cout << "\n[ENGINE] Best Move: " << engineMove << "\n";

    bool capture = isCaptureMove(engineMove);
    if (capture) {
        string dest = engineMove.substr(2, 2);
        if (!robotCapture(dest)) {
            stopOnRobotFailure("capture removal");
            return;
        }
    }

    if (!robotMove(engineMove)) {
        stopOnRobotFailure("piece movement");
        return;
    }

    applyMove(engineMove);
}

void Game::start() {
    cout << "\n===== CHESS ROBOT =====\n";
    cout << "\nHuman = White";
    cout << "\nRobot = Black\n";

    if (!robotRest()) {
        stopOnRobotFailure("startup rest");
    }

    while (!gameOver) {
        printTurn();
        handleHumanMove();

        if (gameOver) {
            break;
        }

        printTurn();
        handleRobotMove();

        if (gameOver) {
            break;
        }

        if (!robotRest()) {
            stopOnRobotFailure("post-move rest");
            break;
        }
    }

    cout << "\n===== GAME ENDED =====\n";
}
