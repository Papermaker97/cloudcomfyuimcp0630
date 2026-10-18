// Fill these in before uploading. Keep the real values out of git (copy to config.local.h if you like).
#pragma once

#define DEVICE_ID      "ppomo-01"

// Wi-Fi: a WPA2 personal network (phone hotspot works). NYU's enterprise Wi-Fi needs a registered device.
#define WIFI_SSID      "your-wifi"
#define WIFI_PASSWORD  "your-password"

// Supabase project (Settings > API). The anon key may only INSERT into squeezes (see ../../web/schema.sql).
#define SUPABASE_URL   "https://YOUR-PROJECT.supabase.co"
#define SUPABASE_ANON_KEY "YOUR-ANON-KEY"

// Optional where-was-it-squeezed pads (FSR 402 under foam). 0 = pressure sensor only.
#define USE_LOCATION_FSRS 0
