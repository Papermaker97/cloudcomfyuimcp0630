#!/bin/sh
# Host-side simulation of the squeeze state machine (no ESP32 needed).
# Runs the Schematik original and the fixed firmware through the same scenarios.
set -e
cd "$(dirname "$0")"
for v in original fixed; do
  if [ $v = original ]; then src=../main.schematik-original.cpp; def=; else src=../main.cpp; def=-DFIXED; fi
  cat $src reset.inc > /tmp/ppomo-fw-$v.cpp
  g++ -std=c++17 -O1 $def -IArduino -o /tmp/ppomo-sim-$v harness.cpp /tmp/ppomo-fw-$v.cpp
  echo "== $v =="; /tmp/ppomo-sim-$v || true
done
