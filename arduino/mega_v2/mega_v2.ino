// SAOS v2 Mega 2560 firmware (first hardware-facing draft).
// STATUS: compiles with avr-gcc 7.3.0 for Mega 2560 (Arduino IDE 2, 2026-11-05): 16794 B flash (6 %), 758 B RAM (9 %). NOT yet run on hardware.
// Control logic, protocol and calibration come from the tested core (saos_core / saos_proto / saos_calib).
// Everything marked [UNVERIFIED] is a hardware conversion that must be checked against a reference (docs/HARDWARE_TEST_PLAN.md).
#include <avr/wdt.h>
#include <EEPROM.h>
#include <DHT.h>                 // "DHT sensor library" by Adafruit
#include "saos_core.h"
#include "saos_proto.h"
#include "saos_calib.h"

using namespace saos;

// ---- pin map: recovered from SAOS_Mega_V_9_0_0 / Pins.h and Config.h ------------------------------
static const uint8_t PIN_PH = A0, PIN_TDS = A2, PIN_LDR = A4, PIN_DHT = 4, PIN_TRIG = 6, PIN_ECHO = 7;
static const uint8_t RELAY_PIN[DEVICE_COUNT] = {
    39,   // FAN        RELAY_EXHAUST_FAN
    53,   // PH_UP      RELAY_PH_UP
    51,   // PH_DOWN    RELAY_PH_DOWN
    49,   // NUTRIENT   RELAY_NUTRIENT
    41,   // LIGHT      RELAY_GROW_LIGHT
    47    // TANK_PUMP  RELAY_TANK_PUMP
};
static const uint8_t RELAY_ON = LOW, RELAY_OFF = HIGH;          // v1 Config.h: relay boards are active-low
static const float ADC_REF = 5.0f, ADC_COUNTS = 1023.0f;
static const float TANK_HEIGHT_CM = 12.0f, SENSOR_TO_BOTTOM_CM = 11.5f;   // v1 values; set to the new tank
static const uint32_t LINK_BAUD = 57600;                         // v2: 57600 has -0.79 % error on a 16 MHz AVR (115200 has +2.12 %); see results/uart_timing.md

DHT dht(PIN_DHT, DHT11);
Controller ctl{Limits()};
proto::Decoder decoder;
uint16_t tx_seq = 0;

// ---- measurements ----------------------------------------------------------------------------------
float air_c = NAN, ph = NAN, tds = NAN, level_pct = NAN, lux = 0;
bool level_new = false;
calib::PhCal phcal;
calib::PhCalibrator calibrator;

static float readVolts(uint8_t pin, uint8_t n = 8) {
    analogRead(pin);                                              // discard: ATmega mux keeps charge from the previous channel (v1 note)
    uint32_t s = 0; for (uint8_t i = 0; i < n; ++i) { s += analogRead(pin); delayMicroseconds(200); }
    return (s / (float)n) * ADC_REF / ADC_COUNTS;
}
static float trimmedPh(float temp_c) {                            // 12 samples, drop min and max
    float v[12], mn = 99, mx = -99, sum = 0;
    for (uint8_t i = 0; i < 12; ++i) { v[i] = readVolts(PIN_PH, 1); sum += v[i]; if (v[i] < mn) mn = v[i]; if (v[i] > mx) mx = v[i]; }
    return calib::phFromVoltage(phcal, (sum - mn - mx) / 10.0f, temp_c);
}
static float readLevelPct() {                                     // [UNVERIFIED] geometry from v1; one echo, no filtering here
    digitalWrite(PIN_TRIG, LOW); delayMicroseconds(3); digitalWrite(PIN_TRIG, HIGH); delayMicroseconds(10); digitalWrite(PIN_TRIG, LOW);
    unsigned long us = pulseIn(PIN_ECHO, HIGH, 4000UL);   // 4 ms covers 68 cm; the default 30 ms would block the loop longer than the 64-byte RX buffer drain time at 57600/115200 baud
    if (us == 0) return NAN;
    float cm = us * 0.0343f / 2.0f;
    float pct = (SENSOR_TO_BOTTOM_CM - cm) / TANK_HEIGHT_CM * 100.0f;
    return pct < 0 ? 0 : (pct > 100 ? 100 : pct);
}
static float readTds(float temp_c) {                              // [UNVERIFIED] common DFRobot polynomial, factor 1.0 as in v1
    float v = readVolts(PIN_TDS) / (1.0f + 0.02f * (temp_c - 25.0f));
    return (133.42f * v * v * v - 255.86f * v * v + 857.39f * v) * 0.5f;
}

// ---- calibration storage ---------------------------------------------------------------------------
static const int EE_PH_CAL = 0;
static void loadCal() {
    uint8_t b[calib::CAL_BLOB_BYTES];
    for (size_t i = 0; i < sizeof b; ++i) b[i] = EEPROM.read(EE_PH_CAL + i);
    if (!calib::deserialize(b, phcal)) {                          // no valid stored calibration -> provisional values
        phcal.slope_v_per_ph = -0.2144f; phcal.v7 = 2.2848f; phcal.t_ref_c = 25.0f; phcal.rms_ph = 0; phcal.max_ph = 0; phcal.n = 0; phcal.status = 255;
    }                                                             // provisional = v1 team's own two-point buffer data (4.01 @ 2.925 V, 6.86 @ 2.314 V)
}
static void saveCal() { uint8_t b[calib::CAL_BLOB_BYTES]; calib::serialize(phcal, b); for (size_t i = 0; i < sizeof b; ++i) EEPROM.update(EE_PH_CAL + i, b[i]); }

// USB console:  B<pH>  add a buffer reading (probe in that buffer);  F fit+store;  R reset points;  P print
static void console() {
    static char line[16]; static uint8_t n = 0;
    while (Serial.available()) {
        char c = Serial.read();
        if (c != '\n' && c != '\r') { if (n < sizeof line - 1) line[n++] = c; continue; }
        line[n] = 0; n = 0;
        if (line[0] == 'B') { float bph = atof(line + 1); float t = air_c == air_c ? air_c : 25.0f;   // [UNVERIFIED] air temp used if no water sensor
            calibrator.add(readVolts(PIN_PH, 16), bph, t); Serial.print(F("points ")); Serial.println(calibrator.count()); }
        else if (line[0] == 'F') { calib::PhCal c; uint8_t st = calibrator.fit(c); Serial.print(F("fit status ")); Serial.print(st);
            Serial.print(F(" rms ")); Serial.println(c.rms_ph, 3); if (st == calib::CAL_OK) { phcal = c; saveCal(); Serial.println(F("stored")); } }
        else if (line[0] == 'R') { calibrator.reset(); }
        else if (line[0] == 'P') { Serial.print(F("slope ")); Serial.print(phcal.slope_v_per_ph, 4); Serial.print(F(" v7 ")); Serial.println(phcal.v7, 4); }
    }
}

// ---- actuators -------------------------------------------------------------------------------------
static void applyRelays() { for (uint8_t i = 0; i < DEVICE_COUNT; ++i) digitalWrite(RELAY_PIN[i], ctl.get((Device)i) ? RELAY_ON : RELAY_OFF); }

static void sendTelemetry(uint32_t now) {
    proto::Telemetry t; memset(&t, 0, sizeof t);
    t.t_ms = now;
    t.air_c100 = (int16_t)(isnan(air_c) ? 0 : air_c * 100); t.ph100 = (uint16_t)(isnan(ph) ? 0 : ph * 100);
    t.tds_ppm = (uint16_t)(isnan(tds) ? 0 : tds); t.level10 = (uint16_t)(isnan(level_pct) ? 0 : level_pct * 10); t.lux = (uint16_t)lux;
    for (uint8_t i = 0; i < DEVICE_COUNT; ++i) if (ctl.get((Device)i)) t.relays |= (1 << i);
    t.mode = ctl.autoActive() ? 0 : 1;
    t.valid = (isnan(air_c) ? 0 : 1) | (isnan(ph) ? 0 : 4) | (isnan(tds) ? 0 : 8) | (isnan(level_pct) ? 0 : 16);   // water temp and battery not wired yet -> bits 1 and 5 stay 0
    proto::Message m; proto::pack(t, tx_seq++, m); uint8_t w[proto::MAX_WIRE]; size_t n = proto::encode(m, w);
    Serial2.write(w, n);
}

static void pollLink(uint32_t now) {
    while (Serial2.available()) {
        proto::Message m;
        if (!decoder.feed((uint8_t)Serial2.read(), m) || m.type != proto::COMMAND) continue;
        proto::Command c; if (!proto::unpack(m, c) || c.device >= DEVICE_COUNT) continue;
        ctl.espCommand(now, (Device)c.device, c.value != 0);
        proto::Ack a = { c.t_tx, c.device, c.value, (uint16_t)(millis() - now) };
        proto::Message r; proto::pack(a, tx_seq++, r); uint8_t w[proto::MAX_WIRE]; size_t n = proto::encode(r, w);
        Serial2.write(w, n);
        applyRelays();                                            // act at once, do not wait for the next 1 s tick
    }
}

void setup() {
    for (uint8_t i = 0; i < DEVICE_COUNT; ++i) { digitalWrite(RELAY_PIN[i], RELAY_OFF); pinMode(RELAY_PIN[i], OUTPUT); }   // OFF before output mode: no glitch at boot
    pinMode(PIN_TRIG, OUTPUT); pinMode(PIN_ECHO, INPUT);
    Serial.begin(115200); Serial2.begin(LINK_BAUD);
    dht.begin(); loadCal();
    wdt_enable(WDTO_4S);                                          // a hung loop resets the board; relays default OFF
}

void loop() {
    static uint32_t t_dht = 0, t_lvl = 0, t_tick = 0;
    uint32_t now = millis();
    wdt_reset();
    pollLink(now); console();

    if (now - t_dht >= 2000) { t_dht = now; float v = dht.readTemperature(); air_c = isnan(v) ? NAN : roundf(v); }   // DHT11 integer, 2 s minimum interval
    if (now - t_lvl >= 3000) { t_lvl = now; float p = readLevelPct(); if (!isnan(p)) level_pct = isnan(level_pct) ? p : level_pct + 0.3f * (p - level_pct); level_new = true; }

    if (now - t_tick >= 1000) {                                   // 1 Hz control tick, same as v1 scheduler
        t_tick = now;
        float tc = isnan(air_c) ? 25.0f : air_c;                  // [UNVERIFIED] no water temperature probe wired in the recovered pin map
        float p = trimmedPh(tc); ph = isnan(ph) ? p : ph + 0.2f * (p - ph);
        float td = readTds(tc); tds = isnan(tds) ? td : tds + 0.15f * (td - tds);
        lux = readVolts(PIN_LDR, 4) / ADC_REF * 1000.0f;          // [UNVERIFIED] LDR volts scaled, not lux
        Inputs in; in.air_c = air_c; in.ph = ph; in.tds = tds; in.level = level_pct; in.level_new = level_new; in.hour = 12.0f; in.lux = lux;   // no RTC read yet: light_auto stays off
        level_new = false;
        ctl.tick(now, in); applyRelays(); sendTelemetry(now);
    }
}
