void resetState() {
  squeezeCount = 0; squeezed = false; pressStartedAt = 0; releaseStartedAt = 0; squeezedAt = 0;
  lastSampleAt = 0; lastRawAt = 0; feedbackOn = false; bellyDir = buttDir = 0; pressDelta = 260; releaseDelta = 120;
}
