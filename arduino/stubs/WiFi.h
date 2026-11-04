#pragma once
#include "Arduino.h"
struct WiFi_ { void mode(int); void begin(const char*, const char*); };
extern WiFi_ WiFi;
