#include "chess_map.hpp"
#include <vector>
#include <iostream>

using namespace std;

// 8x8 board [row][col]
static vector<vector<tuple<double,double,double>>> board = {
    // Column A
    {
        {45.8,16.5,6}, {40.8,16.5,5.5}, {35.3,16,5}, {30.3,16,5},
        {25.3,16,5.5}, {20.3,16,5}, {15.8,15.3,4.5}, {10.5,14,4}
    },

    // Column B
    {
        {45,10.7,7}, {40,10.7,6.5}, {35,10.7,6}, {30,10.5,6},
        {25,10.3,6}, {20,10,5.5}, {15,10,5}, {11.2,10,5}
    },

    // Column C
    {
        {45,5.3,6}, {40,5.3,5.5}, {35,5.3,5}, {30,5.3,5},
        {25,5.5,5}, {20,5.5,5}, {16,5.5,5}, {11,5,5}
    },

    // Column D
    {
        {45,0.5,7}, {40,0.5,6.5}, {34.5,0.5,6}, {29.5,0,6},
        {24.5,0,6}, {19.5,1,6}, {15.5,1,5.5}, {11,1,5}
    },

    // Column E
    {
        {45,-5,7}, {40,-4.8,6.5}, {34.5,-4.5,6}, {29.5,-4.2,6},
        {24.5,-4.5,6}, {20,-4,5.5}, {15.5,-3.5,5}, {11,-3.5,4.5}
    },

    // Column F
    {
        {44,-9.5,7}, {39,-9.5,6.5}, {34,-9.5,6}, {28.5,-9.5,6},
        {23.5,-9,6}, {18.5,-8.5,6}, {13.5,-8,5}, {10,-7.5,4}
    },

    // Column G
    {
        {44,-14.5,7}, {39,-14.5,6.5}, {34,-14.5,6}, {29,-14,6},
        {24,-13.5,5.5}, {19,-13,5}, {14,-12.5,4.5}, {9,-11,4}
    },

    // Column H
    {
        {43.8,-20.3,7.5}, {38.5,-20.3, 7}, {33.5,-19.7, 6.5}, {28.5,-19.1, 6},
        {23.5,-18.5,6}, {18.5,-18,5.5}, {14,-17,5}, {9,-16,5}
    }
};

bool isValidSquare(const string& sq) {
    if (sq.size() != 2) return false;

    char file = sq[0];
    char rank = sq[1];

    return (file >= 'a' && file <= 'h' &&
            rank >= '1' && rank <= '8');
}

tuple<double,double,double> getCoord(const string& sq) {
    if (!isValidSquare(sq)) {
        throw runtime_error("Invalid square!");
    }

    int row = sq[0] - 'a';   // 'a'→0, 'h'→7
    int col = sq[1] - '1';   // '1'→0, '8'→7

    cout << get<0>(board[row][col]) << ", "
         << get<1>(board[row][col]) << ", "
         << get<2>(board[row][col]) << endl;

    return board[row][col];
}