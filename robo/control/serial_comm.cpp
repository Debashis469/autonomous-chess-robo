#include "serial_comm.hpp"

#include <windows.h>

#include <algorithm>
#include <array>
#include <cctype>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

namespace {

constexpr const char* kPortName = "COM7";
constexpr int kBaudRate = 115200;
constexpr DWORD kOpenSettleMs = 1500;
constexpr int kLinePollSleepMs = 10;
constexpr int kBaseTrajectoryTimeoutMs = 5000;
constexpr int kPerWaypointTimeoutMs = 20000;

HANDLE gSerialHandle = INVALID_HANDLE_VALUE;

std::string trimCopy(const std::string& text) {
    size_t start = 0;
    while (start < text.size() &&
           std::isspace(static_cast<unsigned char>(text[start]))) {
        ++start;
    }

    size_t end = text.size();
    while (end > start &&
           std::isspace(static_cast<unsigned char>(text[end - 1]))) {
        --end;
    }

    return text.substr(start, end - start);
}

std::string buildPayload(const std::vector<std::array<std::string, 5>>& traj) {
    std::stringstream ss;

    std::cout << "\n=== Sending Full Trajectory ===\n";

    ss << "[ ";

    for (const auto& step : traj) {
        for (int i = 0; i < 5; i++) {
            std::cout << step[i];
            if (i != 4) std::cout << ", ";
        }
        std::cout << "\n";

        for (int i = 0; i < 5; i++) {
            ss << step[i];
            if (i != 4) ss << " ";
        }
        ss << " ";
    }

    ss << "]\n";

    std::cout << "=== End Trajectory ===\n";
    return ss.str();
}

void clearSerialBuffers(HANDLE handle) {
    PurgeComm(handle, PURGE_RXABORT | PURGE_RXCLEAR | PURGE_TXABORT | PURGE_TXCLEAR);
}

bool configureSerialPort(HANDLE handle, int baudRate) {
    DCB dcb = {0};
    dcb.DCBlength = sizeof(dcb);

    if (!GetCommState(handle, &dcb)) {
        std::cerr << "get state failed\n";
        return false;
    }

    dcb.BaudRate = baudRate;
    dcb.ByteSize = 8;
    dcb.StopBits = ONESTOPBIT;
    dcb.Parity = NOPARITY;
    dcb.fDtrControl = DTR_CONTROL_DISABLE;
    dcb.fRtsControl = RTS_CONTROL_DISABLE;

    if (!SetCommState(handle, &dcb)) {
        std::cerr << "set state failed\n";
        return false;
    }

    COMMTIMEOUTS t = {0};
    t.ReadIntervalTimeout = 50;
    t.ReadTotalTimeoutConstant = 50;
    t.ReadTotalTimeoutMultiplier = 10;
    t.WriteTotalTimeoutConstant = 50;
    t.WriteTotalTimeoutMultiplier = 10;

    if (!SetCommTimeouts(handle, &t)) {
        std::cerr << "set timeouts failed\n";
        return false;
    }

    EscapeCommFunction(handle, CLRDTR);
    EscapeCommFunction(handle, CLRRTS);
    SetupComm(handle, 16384, 16384);
    return true;
}

void drainStartupNoise(HANDLE handle, DWORD durationMs) {
    DWORD start = GetTickCount();
    char buf[128];

    while (GetTickCount() - start < durationMs) {
        DWORD read = 0;
        if (!ReadFile(handle, buf, sizeof(buf), &read, NULL)) {
            return;
        }

        if (read == 0) {
            Sleep(kLinePollSleepMs);
        }
    }
}

bool openPersistentSerialPort() {
    if (gSerialHandle != INVALID_HANDLE_VALUE) return true;

    HANDLE handle = CreateFileA(
        kPortName,
        GENERIC_READ | GENERIC_WRITE,
        0,
        NULL,
        OPEN_EXISTING,
        0,
        NULL
    );

    if (handle == INVALID_HANDLE_VALUE) {
        std::cerr << "open failed\n";
        return false;
    }

    if (!configureSerialPort(handle, kBaudRate)) {
        CloseHandle(handle);
        return false;
    }

    clearSerialBuffers(handle);
    Sleep(kOpenSettleMs);
    drainStartupNoise(handle, 250);
    clearSerialBuffers(handle);

    gSerialHandle = handle;
    std::cout << "[SERIAL] Connected to " << kPortName << "\n";
    return true;
}

bool sendSerialData(HANDLE handle, const std::string& data) {
    DWORD written = 0;

    if (!WriteFile(handle, data.c_str(), static_cast<DWORD>(data.size()), &written, NULL)) {
        std::cerr << "write failed\n";
        return false;
    }

    if (!FlushFileBuffers(handle)) {
        std::cerr << "flush failed\n";
        return false;
    }

    return written == data.size();
}

enum class AckState {
    Pending,
    Success,
    Failure
};

AckState classifyArduinoLine(const std::string& rawLine) {
    std::string line = trimCopy(rawLine);
    if (line.empty()) return AckState::Pending;

    std::cout << "[ARDUINO] " << line << "\n";

    if (line == "1" || line == "DONE") return AckState::Success;
    if (line == "0" || line == "FAIL" || line == "ERR" ||
        line.find("Timeout") != std::string::npos ||
        line.find("Stopped.") != std::string::npos) {
        return AckState::Failure;
    }

    return AckState::Pending;
}

bool waitForTrajectoryResult(HANDLE handle, int timeoutMs) {
    std::string line;
    char buf[128];
    DWORD start = GetTickCount();

    while (GetTickCount() - start < static_cast<DWORD>(timeoutMs)) {
        DWORD read = 0;
        if (!ReadFile(handle, buf, sizeof(buf), &read, NULL)) {
            std::cerr << "read failed\n";
            return false;
        }

        if (read == 0) {
            Sleep(kLinePollSleepMs);
            continue;
        }

        for (DWORD i = 0; i < read; ++i) {
            char c = buf[i];

            if (c == '\r') continue;

            if (c == '\n') {
                AckState state = classifyArduinoLine(line);
                if (state == AckState::Success) return true;
                if (state == AckState::Failure) return false;
                line.clear();
                continue;
            }

            line += c;
        }
    }

    if (!trimCopy(line).empty()) {
        AckState state = classifyArduinoLine(line);
        if (state == AckState::Success) return true;
        if (state == AckState::Failure) return false;
    }

    std::cerr << "[SERIAL] Timed out waiting for robot completion\n";
    return false;
}

int computeTrajectoryTimeoutMs(size_t waypointCount) {
    return kBaseTrajectoryTimeoutMs +
           static_cast<int>(waypointCount) * kPerWaypointTimeoutMs;
}

} // namespace

bool initializeRobotSerial() {
    return openPersistentSerialPort();
}

void shutdownRobotSerial() {
    if (gSerialHandle == INVALID_HANDLE_VALUE) return;

    CloseHandle(gSerialHandle);
    gSerialHandle = INVALID_HANDLE_VALUE;
    std::cout << "[SERIAL] Connection closed\n";
}

bool sendTrajectory(const std::vector<std::array<std::string, 5>>& traj) {
    if (traj.empty()) {
        std::cerr << "[SERIAL] Refusing to send empty trajectory\n";
        return false;
    }

    if (!openPersistentSerialPort()) {
        return false;
    }

    clearSerialBuffers(gSerialHandle);

    std::string payload = buildPayload(traj);
    if (!sendSerialData(gSerialHandle, payload)) {
        return false;
    }

    int timeoutMs = computeTrajectoryTimeoutMs(traj.size());
    bool ok = waitForTrajectoryResult(gSerialHandle, timeoutMs);

    if (ok) {
        std::cout << "[SERIAL] Trajectory completed successfully\n";
    } else {
        std::cout << "[SERIAL] Trajectory failed or timed out\n";
    }

    return ok;
}
