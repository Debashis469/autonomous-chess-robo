#ifndef GAME_HPP
#define GAME_HPP

#include <string>

#include "../engine/board/board.hpp"

class Game {
private:
    Board board;
    bool gameOver;

    bool isValidMoveFormat(const std::string& move);
    bool isLegalMove(const std::string& move);
    bool isCaptureMove(const std::string& move);

    void applyMove(const std::string& move);

    void handleHumanMove();
    void handleRobotMove();
    void printTurn();
    void stopOnRobotFailure(const std::string& context);

public:
    Game();
    ~Game();

    void start();
};

#endif
