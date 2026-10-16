// Host simulation of nano33-flex-test.ino: feeds synthetic flex-sensor signals and checks the count.
// Run: ./run.sh
#include <Arduino.h>
#include <cstdio>
uint32_t g_now = 0; int g_led = 0; std::string g_log; SerialStub Serial;
std::function<int(int, uint32_t)> g_signal;
void setup(); void loop(); extern unsigned long squeezeCount; void resetState();

static int noise(uint32_t t) { return (int)(12 * std::sin(t * 0.37) + 7 * std::sin(t * 1.13)); }
// 0..1 bend: rise over `up` ms, hold, fall over `down` ms
static float ramp(uint32_t t, uint32_t t0, uint32_t up, uint32_t hold, uint32_t down) {
  if (t < t0) return 0; t -= t0;
  if (t < up) return (float)t / up; t -= up;
  if (t < hold) return 1; t -= hold;
  if (t < down) return 1 - (float)t / down;
  return 0;
}
struct Sc { const char *name; int expected; uint32_t dur; std::function<float(uint32_t)> bend; };

int main() {
  const Sc sc[] = {
    {"quick squeeze", 1, 5000, [](uint32_t t) { return ramp(t, 2000, 80, 300, 80); }},
    {"20 normal squeezes", 20, 18000, [](uint32_t t) { float v = 0; for (int i = 0; i < 20; i++) v += ramp(t, 2000 + i * 700, 60, 200, 60); return v; }},
    {"slow squeeze (2 s ramp)", 1, 8000, [](uint32_t t) { return ramp(t, 2000, 2000, 500, 1000); }},
    {"hold 10 s then release", 1, 16000, [](uint32_t t) { return ramp(t, 2000, 100, 10000, 100); }},
    {"stays 30% bent after release, then 3 more", 4, 14000, [](uint32_t t) {
       float v = ramp(t, 2000, 80, 300, 80) + (t > 2460 ? 0.3f : 0.0f);
       for (int i = 0; i < 3; i++) v += ramp(t, 9000 + i * 1000, 60, 200, 60);
       return v; }},
    {"rapid squeezes (4/s) x8", 8, 6000, [](uint32_t t) { float v = 0; for (int i = 0; i < 8; i++) v += ramp(t, 2000 + i * 250, 30, 60, 30); return v; }},
    {"noise only", 0, 20000, [](uint32_t) { return 0.0f; }},
  };
  int fails = 0;
  for (int polarity : {+1, -1}) {
    printf("-- flex reading goes %s when bent --\n", polarity > 0 ? "UP" : "DOWN");
    for (const auto &s : sc) {
      resetState(); g_now = 0; g_log.clear();
      auto bend = s.bend;
      g_signal = [bend, polarity](int pin, uint32_t t) {
        int n = noise(t + (pin == A1 ? 99 : 0));
        if (pin == A1) return 2000 + n;                         // butt sensor stays at rest
        return 2000 + polarity * (int)(bend(t) * 600) + n;      // a firm squeeze bends ~600 counts
      };
      setup();
      while (g_now < s.dur) { loop(); g_now += 1; }             // real hardware time advances by itself
      bool ok = (int)squeezeCount == s.expected;
      if (!ok) fails++;
      printf("  %-44s expected %2d  got %2lu  %s\n", s.name, s.expected, squeezeCount, ok ? "OK" : "<-- WRONG");
    }
  }
  printf("failures: %d\n", fails);
  return fails;
}
