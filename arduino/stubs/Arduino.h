// Minimal Arduino API stubs so the sketches can be syntax/type-checked on a PC. Not a simulator.
#pragma once
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>
#define LOW 0
#define HIGH 1
#define INPUT 0
#define OUTPUT 1
#define A0 54
#define A2 56
#define A4 58
#define F(x) x
#define PROGMEM
#define SERIAL_8N1 0
#define WIFI_STA 1
typedef unsigned long ulong_t;
uint32_t millis(); void delayMicroseconds(unsigned); void pinMode(uint8_t, uint8_t); void digitalWrite(uint8_t, uint8_t);
int analogRead(uint8_t); unsigned long pulseIn(uint8_t, uint8_t, unsigned long);
struct Stream_ { void begin(uint32_t, int = 0, int = -1, int = -1); int available(); int read(); void write(const uint8_t*, size_t);
  template<class T> void print(T); template<class T> void println(T); void print(float, int); void println(float, int); };
extern Stream_ Serial, Serial2;
struct String { String(const char* = ""); bool operator==(const char*) const; };
