#!/bin/sh
# Host simulation of nano33-flex-test.ino (no board needed)
set -e
cd "$(dirname "$0")"
(echo '#include <Arduino.h>'; cat ../nano33-flex-test.ino reset.inc) > /tmp/ppomo-flex-fw.cpp
g++ -std=c++17 -O1 -Istub -o /tmp/ppomo-flex-sim harness.cpp /tmp/ppomo-flex-fw.cpp
/tmp/ppomo-flex-sim
