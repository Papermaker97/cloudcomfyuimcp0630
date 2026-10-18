// Host test for squeeze_detector.h with synthetic pressure inside a sealed squishy body.
// Run: ./run.sh
#include <cstdio>
#include <cmath>
#include <functional>
#include "../ppomo-device/squeeze_detector.h"

static const float AMBIENT = 101325;
static float noise(uint32_t t) { return 4 * std::sin(t * 0.37f) + 3 * std::sin(t * 1.13f); }   // ~ +-7 Pa
// 0..1 squeeze: rise over up ms, hold, fall over down ms
static float ramp(uint32_t t, uint32_t t0, uint32_t up, uint32_t hold, uint32_t down) {
  if (t < t0) return 0;
  t -= t0;
  if (t < up) return (float)t / up;
  t -= up;
  if (t < hold) return 1;
  t -= hold;
  if (t < down) return 1 - (float)t / down;
  return 0;
}
struct Sc { const char *name; int expected; uint32_t dur; std::function<float(uint32_t)> pa; };

int main() {
  const float SQ = 1500;   // a firm squeeze: +1.5 kPa
  const Sc sc[] = {
    {"quick squeeze", 1, 4000, [&](uint32_t t) { return SQ * ramp(t, 1000, 80, 250, 80); }},
    {"20 normal squeezes", 20, 16000, [&](uint32_t t) { float v = 0; for (int i = 0; i < 20; i++) v += SQ * ramp(t, 1000 + i * 700, 60, 200, 60); return v; }},
    {"light squeezes (+300 Pa) x5", 5, 8000, [&](uint32_t t) { float v = 0; for (int i = 0; i < 5; i++) v += 300 * ramp(t, 1000 + i * 1000, 80, 250, 80); return v; }},
    {"slow squeeze (2 s ramp)", 1, 8000, [&](uint32_t t) { return SQ * ramp(t, 1000, 2000, 500, 1000); }},
    {"rapid squeezes (4/s) x8", 8, 5000, [&](uint32_t t) { float v = 0; for (int i = 0; i < 8; i++) v += SQ * ramp(t, 1000 + i * 250, 30, 60, 30); return v; }},
    {"10 s hold in a leaky shell, release, 3 more", 4, 20000, [&](uint32_t t) {
       // a leaky shell (time constant 20 s): during the hold it loses air, after release it reads
       // below ambient and seeps back in with the same time constant
       float v = 0;
       if (t >= 1000 && t < 11100) v = SQ * ramp(t, 1000, 100, 9900, 100) * expf(-(float)(t - 1000) / 20000.0f);
       if (t >= 11100) v = -SQ * (1 - expf(-10100 / 20000.0f)) * expf(-(float)(t - 11100) / 20000.0f);
       for (int i = 0; i < 3; i++) v += SQ * ramp(t, 14000 + i * 1200, 60, 200, 60);
       return v; }},
    {"hand warming +400 Pa over 60 s, no squeeze", 0, 70000, [](uint32_t t) { return 400 * fminf(1, t / 60000.0f); }},
    {"hand warming + 5 squeezes on top", 5, 70000, [&](uint32_t t) { float v = 400 * fminf(1, t / 60000.0f); for (int i = 0; i < 5; i++) v += SQ * ramp(t, 10000 + i * 10000, 80, 250, 80); return v; }},
    {"weather drift -150 Pa/10 min, no squeeze", 0, 120000, [](uint32_t t) { return -150 * (t / 600000.0f); }},
    {"noise only", 0, 30000, [](uint32_t) { return 0.0f; }},
    {"tap/bump spike 20 ms (not a squeeze)", 0, 4000, [&](uint32_t t) { return SQ * ramp(t, 1000, 5, 10, 5); }},
  };
  int fails = 0;
  const uint32_t DT = 10;
  for (const auto &s : sc) {
    SqueezeDetector det;
    det.begin(AMBIENT);
    int count = 0;
    for (uint32_t t = 0; t < s.dur; t += DT)
      if (det.update(AMBIENT + s.pa(t) + noise(t), t, DT)) count++;
    bool ok = count == s.expected;
    if (!ok) fails++;
    printf("  %-46s expected %2d  got %2d  %s\n", s.name, s.expected, count, ok ? "OK" : "<-- WRONG");
  }
  printf("failures: %d\n", fails);
  return fails;
}
