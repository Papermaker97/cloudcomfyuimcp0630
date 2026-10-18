# Ppomo device (final-goal design)

Count squeezes → stamp date/time → show on the web. Read **DESIGN.md** first.

| File | What |
|---|---|
| `DESIGN.md` | Requirements, sensor choice, BOM, wiring, firmware, web, test plan, questions for review |
| `wiring.svg` / `wiring.png` | Wiring diagram |
| `firmware/ppomo-device/` | ESP32-C3 firmware (Arduino). Fill in `config.h` first |
| `firmware/test/run.sh` | Host test of the squeeze detector (no hardware) |
| `web/schema.sql` | Supabase table + access rules |
| `web/dashboard.html` | Web dashboard (demo data until connected) |

Arduino setup:
1. Install the board package **esp32 by Espressif** and pick the board **XIAO_ESP32C3**.
2. Install the libraries **SparkFun BMP581 Arduino Library**, **RTClib** and **Adafruit DRV2605 Library**.

Checked: it compiles with esp32 core 3.3.12 (90% of the default app partition). It has not been run on real hardware yet.
