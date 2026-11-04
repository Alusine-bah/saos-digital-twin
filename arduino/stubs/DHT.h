#pragma once
#include "Arduino.h"
#define DHT11 11
struct DHT { DHT(uint8_t, uint8_t); void begin(); float readTemperature(); };
