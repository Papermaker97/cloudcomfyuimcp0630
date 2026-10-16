#pragma once
#include <cstdint>
struct Preferences { uint32_t v = 0; bool begin(const char *, bool) { return true; } uint32_t getULong(const char *, uint32_t d) { return d; } void putULong(const char *, uint32_t x) { v = x; } };
