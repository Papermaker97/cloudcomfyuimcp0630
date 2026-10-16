void resetFirmwareState() {
  squeezeCount = 0; squeezed = false; pressStartedAt = 0; releaseStartedAt = 0; lastSampleAt = 0;
#ifdef FIXED
  squeezedAt = 0; motorOn = false; motorOnAt = 0;
#else
  motorOffAt = 0;
#endif
}
