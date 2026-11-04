# SAOS digital twin: handover (read this first)

## What this is
A software-only rebuild of the IUT capstone aquaponics controller (Arduino Mega 2560 + ESP32), made after the prototype was dismantled and the
latest firmware lost. It keeps the idea alive, gives benchmark values for a possible second project, and can be rebranded.
The capstone thesis was a degree requirement, not a publication; the new paper (`Lessons_Learned_Redesign_Aquaponics_IoT.pdf`) is the publishable direction.

## Where things are
| Need | Location |
|---|---|
| Run everything | `python -m pytest -q tests`, `make -C core test`, `python run_benchmarks.py`, `python validation/run_validation.py` |
| What the old firmware really did vs the thesis | `FINDINGS.md` |
| Plant/sensor/climate/pH models and their sources | `docs/LITERATURE.md`, `saos_sim/config.py` (every value tagged) |
| Control logic (portable C++ and Python reference) | `core/`, `saos_sim/controller.py`, parity test `tests/test_parity.py` |
| Link protocol v2, gateway, pH calibration | `core/src/saos_proto.cpp`, `saos_gateway.cpp`, `saos_calib.cpp` |
| Benchmarks and pass/fail requirements | `results/summary.md`, `results/validation.md`, `results/redesign_study.md`, `results/link_benchmark.md` |
| Hardware drafts and bench test plan | `arduino/`, `docs/HARDWARE_TEST_PLAN.md`, `tools/serial_logger.py` |
| Roadmap | `docs/V2_REBUILD_PLAN.md` |

## Trust levels (important)
* **Recovered from files** (old, not the final firmware): control limits, pin map, filter constants, relay polarity, ESP32 behaviour.
* **Cited from literature**: alkalinity use, ventilation rates, greenhouse time constant, DHT11 accuracy, tilapia temperature band.
* **Estimated**: tank volume, fish number, feed, fan airflow, ambient temperature, loads, dosing strength.
* **Never measured**: dissolved oxygen, ammonia, nitrate, pressure (constants in v1). All results are simulated.

## Known open items
Compile with avr-gcc / ESP32 toolchain; wire water temperature, battery sensing, RTC; run `docs/HARDWARE_TEST_PLAN.md`;
literature topics 1-6 done (pH, climate, water loss, TDS, power, UART timing); remaining weak spots are listed under 'Not found' in each topic of `docs/LITERATURE.md`.
Replace estimates with measurements in `config.py` and rerun the validation.

## Security
Never commit Wi-Fi passwords or API keys (`arduino/esp32_gateway/wifi_secrets.h` is git-ignored).
