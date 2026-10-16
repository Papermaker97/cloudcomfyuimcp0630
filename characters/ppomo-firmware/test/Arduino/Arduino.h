// Minimal host-side stand-ins for the Arduino/ESP32 APIs used by main.cpp
#pragma once
#include <cstdint>
#include <cstdio>
#include <string>
#include <functional>
#define OUTPUT 1
#define HIGH 1
#define LOW 0
extern uint32_t g_now; extern int g_motor; extern int g_count_msgs; extern std::string g_log;
extern std::function<int(int, uint32_t)> g_signal;
inline uint32_t millis() { return g_now; }
inline void delay(uint32_t ms) { g_now += ms; }
inline void pinMode(int, int) {}
inline void digitalWrite(int, int v) { g_motor = v; }
inline void analogReadResolution(int) {}
inline int analogRead(int pin) { g_now += 0; return g_signal(pin, g_now); }
struct SerialStub {
  void begin(int) {}
  template <class T> void print(T v) { g_log += std::to_string(v); }
  void print(const char *s) { g_log += s; }
  template <class T> void println(T v) { print(v); g_log += "\n"; }
  void println(const char *s) { g_log += s; g_log += "\n"; if (std::string(s).find("\"}") != std::string::npos) g_count_msgs++; }
};
extern SerialStub Serial;
