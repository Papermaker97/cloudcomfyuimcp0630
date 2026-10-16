#include <Arduino.h>
#include <cmath>
uint32_t g_now = 0; int g_motor = 0; int g_count_msgs = 0; std::string g_log; SerialStub Serial;
std::function<int(int, uint32_t)> g_signal;
void setup(); void loop(); extern uint32_t squeezeCount;

// one scenario = belly signal over time (butt stays at rest). Rest ~1000, a firm squeeze ~ +600.
struct Scenario { const char *name; int expected; std::function<int(uint32_t)> belly; uint32_t duration; };
static int noise(uint32_t t) { return (int)(8 * std::sin(t * 0.37) + 5 * std::sin(t * 1.13)); }
static int ramp(uint32_t t, uint32_t t0, uint32_t up, uint32_t hold, uint32_t down, int amp) {
  if (t < t0) return 0; t -= t0;
  if (t < up) return amp * (int)t / (int)up; t -= up;
  if (t < hold) return amp; t -= hold;
  if (t < down) return amp - amp * (int)t / (int)down;
  return 0;
}
int main() {
  Scenario sc[] = {
    {"quick squeeze x1", 1, [](uint32_t t) { return 1000 + noise(t) + ramp(t, 2000, 80, 300, 80, 600); }, 5000},
    {"20 normal squeezes", 20, [](uint32_t t) { int v = 0; for (int i = 0; i < 20; i++) v += ramp(t, 2000 + i * 700, 60, 200, 60, 600); return 1000 + noise(t) + v; }, 18000},
    {"slow squeeze (2 s ramp)", 1, [](uint32_t t) { return 1000 + noise(t) + ramp(t, 2000, 2000, 500, 1000, 600); }, 8000},
    {"hold 10 s then release", 1, [](uint32_t t) { return 1000 + noise(t) + ramp(t, 2000, 100, 10000, 100, 600); }, 16000},
    {"foam stays compressed (+180 after release), then 3 more squeezes", 4, [](uint32_t t) {
       int v = ramp(t, 2000, 80, 300, 80, 600);
       if (t > 2460) v = 180 + ramp(t, 9000, 60, 200, 60, 600) + ramp(t, 10000, 60, 200, 60, 600) + ramp(t, 11000, 60, 200, 60, 600);
       return 1000 + noise(t) + v; }, 14000},
    {"rapid squeezes (4/s) x8", 8, [](uint32_t t) { int v = 0; for (int i = 0; i < 8; i++) v += ramp(t, 2000 + i * 250, 30, 60, 30, 600); return 1000 + noise(t) + v; }, 6000},
    {"noise only", 0, [](uint32_t t) { return 1000 + 3 * noise(t); }, 20000},
  };
  int fails = 0;
  for (auto &s : sc) {
    // fresh state: re-run setup with a reset of the globals the firmware owns
    extern void resetFirmwareState(); resetFirmwareState();
    g_now = 0; g_count_msgs = 0; g_log.clear();
    auto belly = s.belly;
    g_signal = [belly](int pin, uint32_t t) { return pin == 3 ? belly(t) : 1000 + noise(t + 99); };
    setup();
    while (g_now < s.duration) loop();
    bool ok = (int)squeezeCount == s.expected;
    if (!ok) fails++;
    printf("  %-62s expected %2d  got %2u  %s\n", s.name, s.expected, squeezeCount, ok ? "OK" : "<-- WRONG");
  }
  return fails;
}
