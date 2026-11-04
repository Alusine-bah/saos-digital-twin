#pragma once
#include "Arduino.h"
struct EEPROM_ { uint8_t read(int); void update(int, uint8_t); };
extern EEPROM_ EEPROM;
