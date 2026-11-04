# Thesis vs recovered firmware (SAOS_Mega_V_9_0_0)

Source of truth for "firmware" = `Config.h`, `ActuatorManager.cpp`, `WaterLevelSensor.cpp`,
`SAOS_Mega_V_9_0_0.ino` and the sensor drivers in the recovered zip.

| Item | Thesis / earlier paper | Firmware as recovered |
|---|---|---|
| pH control band | 6.8-7.4 | **6.5-7.2** (`PH_LOW_LIMIT`, `PH_HIGH_LIMIT`) |
| Tank pump hysteresis | 30 % on / 40 % off | **40 % on / 70 % off** (hard-coded in `readWaterLevel()`); `TANK_LOW/HIGH_LEVEL` 20/75 in Config.h are unused |
| TDS control | not specified | **600 / 620 ppm** (20 ppm hysteresis, relay chatter risk) |
| Fan control | water/air temperature | **DHT11 air temperature, 30 on / 28 off**; `WATER_TEMP_FAN_*` and `DS_TEMP_*` unused |
| Grow light | automatic | **No automatic control** on the Mega; manual / ESP32 only. The LCD "Fan" icon reads an unused flag |
| Heater, aerator, storage pump, drain pump, buzzer | actuators | Relay pins **are assigned** in `Pins.h` (37, 33, 35, 32, 31) and heater, storage pump and air pump are toggled one at a time in the `actuatorDiag1()` test routine. In normal firmware they are only logical flags from ESP32 commands, never driven by AUTO control, and not in the relay telemetry |
| Dissolved oxygen | measured | **Fixed 0.0**; never written |
| Pressure | measured | **Fixed 1008.5 hPa** in `Globals.h` |
| Ammonia, nitrate | measured | **Fixed 0.0**; never written (nitrate is sent twice in the frame) |
| Mega-ESP32 baud | 115200 | **`Serial2.begin(9600)`**; one 44-field frame is about 0.2 s on the wire |
| Telemetry rate | ~0.55 frames/s measured | Firmware timer is **1 Hz**; the gap is unexplained (blocking TX at 9600, LCD I2C, or receive-side drops) |
| Reported latency 2 ms | | At 9600 baud one byte takes 1.04 ms, so 2 ms is not the transit time of a full frame; the metric needs a definition |
| Battery SoC | | Linear map of voltage 11.0-14.4 V (not coulomb counting) |
| Tank height | | `TANK_HEIGHT` 12 cm, `SENSOR_TO_BOTTOM` 11.5 cm: a small prototype tank, so 1 % is about 1.2 mm of water |
| pH calibration | | Single constant `PH_CALIBRATION` 21.34, fixed slope -5.70 V/pH, no temperature compensation |

## Sensor chain facts used in the simulator
DHT11 integer, read every 2 s; pH 12-sample trimmed mean + IIR 0.20 each 1 s; TDS IIR 0.15 twice/s
with DFRobot polynomial; level SR04 IIR 0.30 every 3 s.

## ESP32 gateway (SAOS_ESP32_V_9_0_2) findings
| Item | Finding |
|---|---|
| UART baud | `MegaSerial.begin(9600)` on GPIO16 (RX) / GPIO17 (TX); matches the Mega's `Serial2.begin(9600)`. The thesis figure of 115200 is wrong. |
| `SPSAS_MODE = SPSAS_SIMULATION_MODE` | Defined in `SystemOS.h` but never referenced anywhere else, so it has no effect: the dashboard shows real UART data, not generated data. Rename or remove it to avoid confusion. |
| DHT11 | Single source is the Mega (fields 0 and 1). The `dht22` JSON/UI names are aliases of the DHT11 values. The thesis/paper must not call it a DHT22. |
| ESP32 AUTO limits | Water level 30/60 %, air 29/32 C, water 24/28 C, DO 5/7, TDS 500/800, pH 6.5/6.8 and 7.5/7.2, 1 s interval. These differ from the Mega limits (level 40/70, air 28/30, TDS 600/620, pH 6.5/7.2). Two controllers with different limits means the behaviour depends on which one owns the actuators. |
| DO control | `dissolvedOxygen` rule exists in the ESP32 controller but the Mega always sends 0.0, so it can never act on real data. |
| Credentials | `WiFiConfig.h` contains a hard-coded Wi-Fi password and an AP password in the source. Move them into the `*.local.h` files and keep them out of any public repository or paper. |

## Device-test archive findings (SAOS_DEVICE_TESTS)
| Item | Finding |
|---|---|
| pH calibration | Production firmware uses a tutorial constant (`PH_CALIBRATION` 21.34, slope -5.70). Your own two-point buffer test (pH 4.01 at 2.925 V, pH 6.86 at 2.314 V) gives slope -4.664 pH/V, intercept 17.654. With the production formula those buffers would read 4.67 and 8.15 (errors +0.66 and +1.29). If the buffer data describe the installed probe, the firmware reads about 8.3 when true pH is 7.0, and AUTO would settle the real pH near 5.5-6.1 |
| Mis-named test files | `NH3_Serial_Monitor_4.ino` is a pH sketch (the tutorial source of the 21.34 constant); `SR_04_Ultrasonic_Sensor1.ino` is an MQ137 sketch |
| MQ137 constants | Test library: clean-air ratio 3.6, slope -0.243, midpoint 0.323, R0 measured. Production `Config.h`: R0 fixed 20, slope -0.263, intercept 0.42. They differ. Either way the sensor measures NH3 in the air, not in the water, and was never calibrated against a reference |
| Soil, TDS, ACS712, LM35 | Starting conversions only: soil dry/wet ADC never recorded, TDS calibration factor left at 1.000, ACS712 zero assumed 2.500 V |


## Fan purpose (designer's statement, 2026-11-04)
The two fans exist to drive heat out of the growing space; the system was designed for indoor and outdoor farming. The thesis wording
that they cool the electronics compartment conflicts with this and probably comes from an earlier (7th-semester) draft. Designer intent is used:
the DHT11 measures grow-area air and the greenhouse heat-balance model applies. Both fans share one relay in the recovered firmware, so they are modelled as one unit.
Fan airflow and enclosure volume are unrecovered: [ESTIMATE] 1.0-1.5 air changes per minute (SRAC 5008). Scenario S11 covers indoor mode [ESTIMATE].

## Update 2026-11-04: September Dhaka ambient (swing 3 C instead of 5 C)
- Validation is now 9 of 12 pass. R6 (relay switching) now passes: fan toggles 0.2/day vs 155 before. The earlier fan-chatter finding depended on the assumed 5 C swing; the paper must say so (hysteresis chatter needs ambient near the 30/28 C thresholds). Air <35 C: 63.1 %, water in 25-30 C: 6.3 % (outdoor), blackout under 30 % sun: 27.9 h.
- redesign_study.md, climate_sensitivity.md and paper numbers were produced with swing 5 and need re-running before they are quoted.
