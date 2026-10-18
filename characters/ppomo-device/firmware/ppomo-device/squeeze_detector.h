// One squeeze = one event, from a single pressure signal (Pa) inside the sealed body.
// No Arduino dependencies, so the same file runs in the host test (../test/run.sh).
//
// Same rules as the earlier FSR / flex firmware:
//   - a squeeze starts when the signal stays PRESS above the resting value for PRESS_CONFIRM
//   - it can only count again after the signal stays within RELEASE of rest for RELEASE_CONFIRM
//   - the resting value follows slow drift (weather, hand warmth, air seeping back in) while no squeeze
//     is counted, and follows a lower value quickly (air leaked out during a long hold, then let go).
//     A squeeze rises far faster than any drift, so it always gets past PRESS before the rest catches up.
//   - a squeeze that never releases (long hold) re-arms after STUCK_REARM with the current value
//     as the new rest, still one count for the hold
#pragma once
#include <stdint.h>
#include <math.h>

struct SqueezeConfig {
  float pressPa = 200;          // tune on the real shell: firm squeeze of a 95 mm TPU body ~ 1-5 kPa (to measure)
  float releasePa = 80;
  uint32_t pressConfirmMs = 30;
  uint32_t releaseConfirmMs = 120;
  float upTauMs = 4000;         // drift follow; a drift of r Pa/s lags by r * 4 s, so keep r below ~40 Pa/s
  float downTauMs = 200;        // fast follow when the signal drops below rest
  uint32_t stuckRearmMs = 4000;
};

class SqueezeDetector {
 public:
  SqueezeConfig cfg;

  void begin(float restValue) { base_ = restValue; squeezed_ = pressing_ = releasing_ = false; peak_ = 0; }
  float base() const { return base_; }
  bool squeezed() const { return squeezed_; }
  float lastPeakPa() const { return peak_; }   // highest delta of the current / last squeeze

  // Feed one sample taken every dtMs. Returns true on the sample that counts a new squeeze.
  bool update(float value, uint32_t now, float dtMs) {
    const float d = value - base_;
    if (!squeezed_) {
      track(d, dtMs);
      if (d >= cfg.pressPa) {
        if (!pressing_) { pressing_ = true; pressStartedAt_ = now; }
        if (now - pressStartedAt_ >= cfg.pressConfirmMs) {
          squeezed_ = true; pressing_ = releasing_ = false; squeezedAt_ = now; peak_ = d;
          return true;
        }
      } else pressing_ = false;
      return false;
    }
    if (d > peak_) peak_ = d;
    if (d <= cfg.releasePa) {
      if (!releasing_) { releasing_ = true; releaseStartedAt_ = now; }
      if (now - releaseStartedAt_ >= cfg.releaseConfirmMs) { squeezed_ = releasing_ = false; }
    } else {
      releasing_ = false;
      if (now - squeezedAt_ >= cfg.stuckRearmMs) { base_ = value; squeezed_ = false; }
    }
    return false;
  }

 private:
  float base_ = 0, peak_ = 0;
  bool squeezed_ = false, pressing_ = false, releasing_ = false;
  uint32_t pressStartedAt_ = 0, releaseStartedAt_ = 0, squeezedAt_ = 0;

  void track(float d, float dtMs) {
    if (d < 0) base_ += d * fminf(1.0f, dtMs / cfg.downTauMs);
    else if (d < cfg.pressPa) base_ += d * fminf(1.0f, dtMs / cfg.upTauMs);
  }
};
