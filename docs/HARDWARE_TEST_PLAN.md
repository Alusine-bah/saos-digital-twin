# Build and test plan for prototype 2

Status of the code: core, protocol, gateway and calibration are tested on a PC. The sketches in `arduino/` are only syntax-checked
against stubs. Nothing has been compiled with avr-gcc or the ESP32 toolchain, and nothing has run on hardware.
Do the steps in order; each one replaces a simulated or estimated number with a measured one.

## 0. Prepare
1. `sh arduino/sync.sh` copies the tested core into both sketch folders. Open each sketch in the Arduino IDE.
2. Mega: board "Arduino Mega 2560"; install library "DHT sensor library" (Adafruit). ESP32: install the ESP32 board package; copy
   `wifi_secrets.example.h` to `wifi_secrets.h`, set the SSID, password and a long random `API_KEY`.
3. Compile both. Fix any compile error first; record flash and RAM use of the Mega (target under 60 % RAM).
4. Relay boards are active-low (v1 `Config.h`). Before connecting any pump or fan, power the board with relays unloaded and check that all relays are OFF at boot and after a watchdog reset.

## 1. Pin map used by `mega_v2.ino` (from the recovered v1 `Pins.h`)
| Function | Pin | Function | Pin |
|---|---|---|---|
| pH probe | A0 | Exhaust fan relay | 39 |
| TDS probe | A2 | pH up relay | 53 |
| Light sensor | A4 | pH down relay | 51 |
| DHT11 | D4 | Nutrient pump relay | 49 |
| SR04 trig / echo | D6 / D7 | Grow light relay | 41 |
| Link to ESP32 | Serial2 (TX2 16, RX2 17) | Tank pump relay | 47 |
ESP32 side: Serial2 on GPIO16 (RX) and GPIO17 (TX), crossed with the Mega, common ground, and a level shifter or divider on Mega TX2 to ESP32 RX
(5 V to 3.3 V). Not wired in the v2 sketch yet: water temperature, battery and solar sensing, RTC, heater, air pump, storage and drain pumps.

## 2. Bench tests (no fish, no plants)
| Test | How | Pass criterion | Replaces |
|---|---|---|---|
| T1 Link smoke | `python tools/serial_logger.py <port> 57600 300` on the ESP32 side, or on the Mega USB if you wire a spare UART | PDR 100 % on a short wire, 0 CRC errors | simulated link table |
| T2 Link loss | Same, long thin wires and a motor running nearby | CRC errors are detected, never accepted; PDR reported | bit-error assumption |
| T3 Command response | Dashboard `/cmd?dev=fan&val=1&key=...`; log time from request to ACK and to relay click | mean under 1 s (R10); record p95 | 52 ms simulated |
| T4 Watchdog | Hold the fan on, then unplug Wi-Fi | Mega returns to AUTO about 8 s after the last heartbeat | firmware behaviour |
| T5 pH calibration | Buffers 4.01, 6.86, 9.18, same temperature; `B4.01`, `B6.86`, `B9.18`, then `F` over the USB console | fit status 0, RMS under 0.1 pH; check a fourth buffer within 0.1 pH | v1 tutorial constants (error 1.35 pH) |
| T6 pH drift | Re-test weekly; compare slope and v7 with `driftOk()` | slope change under 10 % | none (new) |
| T7 Level sensor | Fill the tank to marked volumes, 10 readings each | error under 3 % full scale, jitter recorded | assumed 0.8 % noise |
| T8 TDS | Compare with a handheld meter in 342 ppm and 1413 uS/cm standards | within 10 % after setting the factor | factor 1.000 |
| T9 DHT11 | Compare with a reference thermometer 20-40 C | record the real bias (the sim shows +/-2 C changes fan behaviour a lot) | `dht_bias_c` |
| T10 Relay life | Log fan toggles per day over a week | under 100 per day (R6) | 156 per day simulated |

## 3. Ask for and record (these set the model)
Tank and system volume, fish number and mass, daily feed, measured alkalinity (KH kit), fan airflow, enclosure volume, pump flow rates,
real loads in watts for each device, panel and battery ratings, and the site's ambient temperature range. Put them into `saos_sim/config.py`
and rerun `python validation/run_validation.py` so simulated and measured behaviour can be compared.

## 4. Before the plants and fish go in
Run the whole system on water only for 7 days. Accept only if: no unexpected AUTO/REMOTE switching, pH inside band, no relay above 100 switches per day,
battery above 20 % overnight, logger PDR above 99 %. Then compare the logged week with the twin's prediction for the same ambient data.
