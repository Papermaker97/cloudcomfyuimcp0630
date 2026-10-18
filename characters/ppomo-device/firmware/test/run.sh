#!/bin/sh
# Host test of the squeeze detector (no hardware needed): ./run.sh
set -e
cd "$(dirname "$0")"
g++ -std=c++17 -O2 -Wall -o /tmp/ppomo-detector-test detector_test.cpp
/tmp/ppomo-detector-test
