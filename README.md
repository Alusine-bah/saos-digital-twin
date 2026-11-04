# SAOS Simulator

Software twin of the SAOS aquaponics controller (Arduino Mega 2560 + ESP32 gateway), built from
the recovered firmware and the thesis, so the design survives the dismantled prototype and can
be used for benchmarking the next version.

## Run
    pip install numpy matplotlib pytest
    python run_benchmarks.py     # writes results/summary.md, results.json, CSVs, PNGs
    python -m pytest -q tests

## What is real and what is assumed
Every parameter in `saos_sim/config.py` is tagged **[THESIS]**, **[FIRMWARE]** or **[ASSUMED]**.
`Config.h` and all sensor drivers have been recovered, so control limits and sensor chains are now [FIRMWARE].
The plant physics, noise levels and load wattages are still [ASSUMED] and must be calibrated on new hardware before being quoted as measurements.
Simulation results are model outputs, not experimental data.

## Firmware facts reproduced (see FINDINGS.md for the thesis comparison)
- 1 Hz decision loop; pH-up/pH-down mutually exclusive, dead band 6.5-7.2, fault guard 2-12
- Fan 30/28 C on DHT11 air temperature; TDS 600/620 ppm; tank pump 40 %/70 % every 3 s
- No automatic grow-light control exists
- Any ESP32 actuator command suspends Mega AUTO; 8 s silence returns to AUTO
- `pressure` is hard-coded 1008.5 and `dissolvedOxygen` is 0 in the firmware, so they are not modelled as measurements

## Layout
- `saos_sim/plant.py` greenhouse, water, pH, TDS, level, solar/battery
- `saos_sim/controller.py` Mega control rules + ESP32 override watchdog
- `saos_sim/link.py` UART frame, serialization time, loss, command response
- `saos_sim/sim.py` runner and metrics; `run_benchmarks.py` scenarios S1-S8

## v2 control core (Stage 1)
`core/` holds the portable C++ controller (`core/include/saos_core.h`, `core/src/saos_core.cpp`): pure C++11, no
Arduino calls, no heap, no STL. Defaults reproduce the v1 firmware; v2 options add anti short-cycle dwell times,
pulse-and-wait pH dosing, RTC photoperiod light control and safe shut-off on invalid sensors.

    make -C core test            # 37 C++ unit checks
    python -m pytest -q tests    # includes second-by-second parity of C++ vs the Python twin

Not yet verified: compilation with avr-gcc for the Mega (no AVR toolchain was available when this was written).

## v2 link protocol (Stage 2)
`core/include/saos_proto.h`: COBS-framed binary frames with CRC-16, sequence numbers, MSG_PING/MSG_PONG, command/ACK with
echoed timestamps (so latency and response time are measured on one clock). 25-byte telemetry payload, 32 bytes on the wire
(v1 was an ASCII frame of roughly 200+ bytes at 9600 baud).

    python run_link_benchmark.py    # results/link_benchmark.md and .png (v1 vs v2 across bit error rates)

Metric definitions used everywhere:
- Delivery ratio = frames received intact / frames sent (gaps found from sequence numbers)
- Telemetry latency = scheduled send time to fully received, one direction
- Command response time = command first sent to ACK fully received (includes retries and Mega loop pick-up)

## v2 pH calibration (Stage 3a)
`core/include/saos_calib.h`: multi-point least-squares calibration (V = v7 + s*(pH-7)), Nernst temperature
compensation, acceptance checks, drift check against the stored calibration, 20-byte EEPROM blob with CRC-16.
Procedure: `docs/PH_CALIBRATION_PROCEDURE.md`. Study: `python studies/ph_calibration_study.py` -> `results/ph_calibration_study.md`.

## Literature-backed pH model (Stage 3b, topic 1)
pH is now driven by an alkalinity budget (`alk_ref_mgl`, `alk_loss_mgl_day`, `alk_loss_from_feed()`), with sources and
derivations in `docs/LITERATURE.md` and the workload sensitivity in `results/ph_drift_sensitivity.md`
(`python studies/ph_drift_sensitivity.py`).

## Climate model (Stage 3b, topic 2)
Air temperature follows a heat balance with fan ventilation (`fan_vent_fraction_from_ach()`); sources in `docs/LITERATURE.md`,
sensitivity in `results/climate_sensitivity.md` (`python studies/climate_sensitivity.py`).

## ESP32 gateway (Stage 4)
`core/include/saos_gateway.h`, `core/src/saos_gateway.cpp`: portable relay between Mega and dashboard. The Mega stays the single
control authority; the gateway holds operator requests with a 2 s heartbeat (Mega watchdog 8 s), tracks ACK/retry, counts delivery
from sequence gaps, and produces the dashboard JSON. Tests: `core/tests/test_gateway.cpp`, `test_gateway_e2e.cpp` (run `make -C core test`).
Mutation check: heartbeat 9 s makes both gateway tests fail.

## Stage 5 validation
`python validation/run_validation.py [days] [seeds]` checks 12 own [DESIGN] requirements over several seeds and writes `results/validation.md`.

## Stage 5b redesign study
`python studies/redesign_study.py` -> `results/redesign_study.md`. Python controller now has the same dwell timers as the C++ core (`min_on_s`, `min_off_s`), parity-tested.

## Stage 7: hardware-facing drafts
`arduino/mega_v2`, `arduino/esp32_gateway` (run `sh arduino/sync.sh` first; syntax-checked against `arduino/stubs` only), `tools/serial_logger.py`
(decodes v2 frames, PDR/CRC report; byte-identical to the C++ encoder, tested), `docs/HARDWARE_TEST_PLAN.md`.

## Water loss (literature topic 3)
`level_loss_per_h` is now 0.17 %/h, derived in `docs/LITERATURE.md`; the old 0.9 was a guess. `python studies/water_loss_sensitivity.py`. The parity coverage test forces a high loss so the tank pump still fires in 2 days.

## TDS (literature topic 4)
`docs/LITERATURE.md` topic 4, `python studies/tds_study.py` -> `results/tds_study.md`. Dwell timers now apply to fan, tank pump and light only (a forced minimum on-time on a dosing pump overshoots).

## Power (literature topic 5)
`docs/LITERATURE.md` topic 5, `python studies/power_study.py` -> `results/power_study.md`. The model now adds 0.36 W coil power per ON relay (cited).

## UART timing (literature topic 6)
`docs/LITERATURE.md` topic 6, `results/uart_timing.md`. v2 sketches now use 57600 baud (best tolerance margin); the gateway paces frames 20 ms apart (tested).

## Live demo
`pip install -r requirements.txt` then `streamlit run app.py`: change weather, fan, pH, TDS, water and power parameters and see the simulated result and pass/fail checks. See `docs/GITHUB_SETUP.md` for GitHub and online hosting.
