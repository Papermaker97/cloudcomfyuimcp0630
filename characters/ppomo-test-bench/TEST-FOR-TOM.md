# Ppomo — first test with school parts

**Question this test answers:** can "one squeeze = one event" be counted reliably from a sensor inside a squishy body, and can each event carry a date and time to a web page?

## Parts
- Arduino Nano 33 IoT
- 2 × flex sensors (shop), 2 × 10 kΩ resistors
- LED + 220 Ω (stands in for the vibration motor)
- A stress ball / foam as the body, plus the PLA print of Ppomo for size

## Wiring
```
3.3V ─ flex (belly) ─┬─ A0        3.3V ─ flex (butt) ─┬─ A1
                     └─ 10k ─ GND                     └─ 10k ─ GND
D2 ─ 220Ω ─ LED ─ GND
```

## Software
- **Firmware:** `../ppomo-firmware/nano33-flex-test/nano33-flex-test.ino` (compiles for the Nano 33 IoT: 19 KB flash, 4 KB RAM).
  - Counting uses hysteresis plus a confirm time.
  - The bend direction is learned on the first squeeze.
  - A long hold re-arms with no extra count.
  - It streams JSON over USB.
  - Host simulation: 14/14 cases pass, for both sensor polarities.
- **Web page:** `index.html` (desktop Chrome, Web Serial). It shows:
  - a live graph with the thresholds, and sliders that tune the device
  - a 7-step test protocol
  - the Ppomo character inflating with the count
  - a **date/time log of every squeeze, with CSV export**

## Protocol (in the page)
1. 20 normal squeezes → 20
2. Hold 10 s → 1
3. Slow squeeze (2 s) → 1
4. Fast squeezes (4/s) ×8 → 8
5. Light squeezes ×5 → 5
6. Leave it alone 60 s → 0
7. Put it down on a table / bump it → 0

## What I want to learn
- How much the flex signal changes when the sensor is inside the body versus taped outside.
- Whether one sensor catches squeezes anywhere on the body. I expect not, which is why the final design uses air pressure (see `../ppomo-device/DESIGN.md`).
- The thresholds that work by hand: these feed the final firmware.
