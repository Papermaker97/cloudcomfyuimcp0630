// Host-side stand-ins for the Arduino APIs used by nano33-flex-test.ino
#pragma once
#include <cstdint>
#include <cmath>
#include <cctype>
#include <string>
#include <functional>
#include <algorithm>
using std::max;
#define OUTPUT 1
#define HIGH 1
#define LOW 0
#define A0 100
#define A1 101
#define LED_BUILTIN 13
extern uint32_t g_now; extern int g_led; extern std::string g_log;
extern std::function<int(int, uint32_t)> g_signal;
inline unsigned long millis() { return g_now; }
inline void delay(unsigned long ms) { g_now += ms; }
inline void pinMode(int, int) {}
inline void digitalWrite(int p, int v) { if (p == 2) g_led = v; }
inline void analogReadResolution(int) {}
inline int analogRead(int pin) { return std::clamp(g_signal(pin, g_now), 0, 4095); }
struct String : std::string {
  String() {} String(const char *s) : std::string(s) {}
  String substring(size_t a) const { return String(substr(a).c_str()); }
  long toInt() const { return atol(c_str()); }
  String &operator+=(char c) { push_back(c); return *this; }
};
struct SerialStub {
  void begin(int) {} explicit operator bool() const { return true; }
  int available() { return 0; } int read() { return -1; }
  void print(const char *s) { g_log += s; }
  void print(int v) { g_log += std::to_string(v); }
  void print(unsigned long v) { g_log += std::to_string(v); }
  void println(const char *s) { g_log += s; g_log += "\n"; }
};
extern SerialStub Serial;
