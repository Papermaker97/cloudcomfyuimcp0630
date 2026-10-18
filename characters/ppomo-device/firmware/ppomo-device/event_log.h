// Append-only squeeze log on the ESP32's flash (LittleFS), so no squeeze is lost while offline.
// Each record has its own sequence number; the uploader sends records after the last acknowledged
// one and the server ignores duplicates, so a retry after a dropped connection is always safe.
#pragma once
#include <Arduino.h>
#include <LittleFS.h>
#include <Preferences.h>

enum : uint8_t { SRC_BODY = 0, SRC_BELLY = 1, SRC_BUTT = 2 };
enum : uint8_t { EV_TIME_VALID = 1 };

struct __attribute__((packed)) SqueezeRecord {
  uint32_t seq;        // 1, 2, 3 ... for the life of the device (= total squeeze count)
  int64_t epochMs;     // UTC milliseconds, valid only when flags & EV_TIME_VALID
  uint32_t uptimeMs;   // millis() at the squeeze, to fix the time later in the same boot
  uint16_t boot;       // boot counter, so uptimeMs is only reused within its own boot
  uint16_t peakPa;     // how hard (highest pressure rise), filled when the squeeze ends
  uint8_t source;      // SRC_*
  uint8_t flags;
};

class EventLog {
 public:
  bool begin() {
    if (!LittleFS.begin(true)) return false;   // formats on first use
    prefs_.begin("ppomo", false);
    lastSeq_ = prefs_.getULong("seq", 0);
    ackedSeq_ = prefs_.getULong("acked", 0);
    boot_ = prefs_.getUShort("boot", 0) + 1;
    prefs_.putUShort("boot", boot_);
    return true;
  }
  uint32_t count() const { return lastSeq_; }
  uint32_t acked() const { return ackedSeq_; }
  uint16_t boot() const { return boot_; }
  bool pending() const { return ackedSeq_ < lastSeq_; }

  uint32_t append(SqueezeRecord r) {
    r.seq = lastSeq_ + 1;
    r.boot = boot_;
    File f = LittleFS.open(PATH, FILE_APPEND);
    if (!f) return 0;
    f.write((const uint8_t *)&r, sizeof r);
    f.close();
    lastSeq_ = r.seq;
    prefs_.putULong("seq", lastSeq_);
    return r.seq;
  }
  // patch the last record (strength is only known once the squeeze is let go)
  void setLastPeak(uint32_t seq, uint16_t peakPa) {
    File f = LittleFS.open(PATH, "r+");
    if (!f || f.size() < sizeof(SqueezeRecord)) return;
    SqueezeRecord r;
    f.seek(f.size() - sizeof r);
    f.read((uint8_t *)&r, sizeof r);
    if (r.seq != seq) { f.close(); return; }
    r.peakPa = peakPa;
    f.seek(f.size() - sizeof r);
    f.write((const uint8_t *)&r, sizeof r);
    f.close();
  }
  // read up to max records with seq > acked
  size_t unsent(SqueezeRecord *out, size_t max) {
    File f = LittleFS.open(PATH, "r");
    if (!f) return 0;
    size_t n = 0;
    SqueezeRecord r;
    while (n < max && f.read((uint8_t *)&r, sizeof r) == sizeof r)
      if (r.seq > ackedSeq_) out[n++] = r;
    f.close();
    return n;
  }
  void ack(uint32_t seq) {
    if (seq <= ackedSeq_) return;
    ackedSeq_ = seq;
    prefs_.putULong("acked", ackedSeq_);
    if (ackedSeq_ >= lastSeq_) LittleFS.remove(PATH);   // everything is on the server, start a fresh file
  }

 private:
  static constexpr const char *PATH = "/squeezes.bin";
  Preferences prefs_;
  uint32_t lastSeq_ = 0, ackedSeq_ = 0;
  uint16_t boot_ = 0;
};
