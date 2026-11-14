// Ppomo sensor test 3: MPXV (A0) + MPX2102ASX (A1 - A2) at the same time
// Wiring: see two-sensors-breadboard.png. Both sensors on 3V3 (NOT 5V).
// Open Tools > Serial Plotter at 9600. Keep still for the first 2 s (baseline), then blow / press.
// Lines: MPXV_mV  = change of the MPXV output in mV
//        MPX2102_x10 = change of the MPX2102 bridge output (A1 - A2) in mV, times 10 (it is tiny)
// Written for the Ppomo project with help from Claude.

const int N = 64;          // readings averaged per sample (smooths noise)
float baseMPXV = 0, baseMPX = 0;

float readMV(int pin) {
  long sum = 0;
  for (int i = 0; i < N; i++) sum += analogRead(pin);
  return (sum / (float)N) * 3300.0 / 4095.0;   // 12-bit, 3.3 V reference
}

void setup() {
  Serial.begin(9600);
  analogReadResolution(12);
  delay(500);
  // baseline: average for 2 seconds while nothing is pressed
  int n = 0;
  unsigned long t0 = millis();
  while (millis() - t0 < 2000) {
    baseMPXV += readMV(A0);
    baseMPX  += readMV(A1) - readMV(A2);
    n++;
  }
  baseMPXV /= n;
  baseMPX  /= n;
  // wiring check, printed once (Serial Monitor shows it; the plotter ignores it)
  // MPXV resting voltage: ~0 or ~3300 mV = wiring problem. MPX2102 difference: should be a few mV at most.
  Serial.print("check MPXV_rest_mV="); Serial.print(baseMPXV, 0);
  Serial.print(" MPX2102_rest_mV="); Serial.println(baseMPX, 2);
}

void loop() {
  float mpxv = readMV(A0);
  float mpx  = readMV(A1) - readMV(A2);
  Serial.print("MPXV_mV:");
  Serial.print(mpxv - baseMPXV, 1);
  Serial.print(" MPX2102_x10:");
  Serial.println((mpx - baseMPX) * 10.0, 1);
  delay(20);
}
