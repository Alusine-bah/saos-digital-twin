# SAOS v2 rebuild plan

Principle: keep what the old files prove works, fix what they show was wrong, and drop what was never real.
Every number in v2 must be [MEASURED], [CITED] or [DESIGN CHOICE]. No silent assumptions.

## A. Keep (verified in the recovered code)
| Item | Why it stays |
|---|---|
| Two-board split: Mega 2560 for sensing and relays, ESP32 for Wi-Fi and dashboard | Sound design; isolates real-time control from the web stack |
| Command protocol with ACK / NACK / STATE replies | Works and is testable |
| 8 s ESP32 ownership watchdog that falls back to local AUTO | Good fail-safe behaviour |
| pH-up and pH-down never on together; sensor-fault guard before dosing | Correct safety logic |
| Hysteresis control for fan, TDS, tank pump | Right pattern (limits need redoing) |
| Non-blocking DS18B20 with ROM lookup, DHT11 range rejection, discard-first ADC reads | Good sensor hygiene |
| Active-low relay outputs, forced OFF at boot | Safe default |
| LittleFS dashboard, REST endpoints, OTA | Reusable, after credentials are removed from source |
| Hardware list and pin map (`Pins.h`) | Reuse as the starting map |
| Evaluation ideas: latency, delivery ratio, response time, power budget, cost | Keep the metrics, measure them properly this time |

## B. Fix (found wrong or unsupported)
| Problem found | v2 requirement |
|---|---|
| Two controllers with different limits (Mega vs ESP32) | One authority (Mega); ESP32 only sends setpoints and manual overrides. One shared limits file |
| pH uses tutorial constants; own buffer data disagrees | Two-point (4.01 / 6.86 / 9.18) calibration stored in EEPROM, temperature compensated, drift check |
| Link at 9600 baud, no CRC, no sequence number, latency undefined | 57600 baud (best AVR error margin, results/uart_timing.md), framed with CRC and sequence number, timestamp echo so latency, PDR and response time are measured, not guessed |
| Fan 28/30 C short-cycling risk, 2 C DHT11 error | Minimum on/off time, wider band, DS18B20 air sensor |
| TDS band 600-620 ppm | Band sized to sensor noise and crop target |
| No automatic grow light, though RTC exists | RTC-based photoperiod with lux override |
| Battery SoC from voltage only | Coulomb counting with the ACS712 plus voltage correction |
| Credentials in source | `*.local.h` only, never committed |
| Frame has duplicated fields (nitrate twice, light twice) | Named JSON-or-binary frame with versioned schema |

## C. Drop or make real
| Item | Decision |
|---|---|
| Dissolved oxygen, pressure, nitrate, nitrite, CO2 | Drop from v2 unless a real sensor is added; never transmit a constant as a measurement |
| Ammonia (MQ137) | Keep only as air-quality indicator, labelled as such |
| Heater, air pump, storage pump, drain pump | Pins exist: either wire them into AUTO control with defined rules or remove them |
| `SPSAS_MODE` simulation macro | Replace with a real build flag (HIL / field) |
| Soil moisture display with no control | Either add irrigation control or remove |

## D. Stages (one at a time)
0. This document and the findings table. (done)
1. Portable control core in C++ (no Arduino calls), unit-tested on the PC, with the Python twin as the reference model; parity tests between both. (done on the PC: 37 unit checks and 15 tests; AVR build still to verify)
2. Protocol v2 on both boards plus a loopback logger that measures latency, delivery ratio and response time. (codec, tests and simulated link benchmark done on the PC; on-board firmware and real-hardware measurement still to do)
3. Sensor models and calibration procedures (pH calibration module and study done; remaining sensors and the literature values still to do); replace [ASSUMED] plant values with [CITED] ones from the literature search, one topic at a time.
4. ESP32 gateway and dashboard on top of protocol v2.
5. Validation runs, simulated first, then hardware-in-the-loop when parts are available again.
6. Paper v2: a corrected, honest account that uses the simulator results and the lessons learned.
