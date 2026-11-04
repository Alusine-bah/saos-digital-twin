# pH probe calibration procedure (v2)

Status of each item: [DESIGN] = my proposed value, to be confirmed against the probe datasheet and the literature search.

**Equipment:** fresh pH 4.01, 6.86 and 9.18 buffers (3-point) or 4.01 and 6.86 (minimum), a clean cup per buffer, distilled water for rinsing, the DS18B20 for temperature.

**Steps**
1. Warm up the module for at least 10 minutes with the probe in storage solution or the tank. [DESIGN]
2. Rinse the probe in distilled water, blot (do not wipe), place in buffer 6.86. Record the voltage when it changes by less than 2 mV over 30 s. [DESIGN] Add the point with the DS18B20 temperature.
3. Repeat for 4.01, then 9.18 (rinse between every buffer).
4. Keep all buffers within 5 C of each other; the firmware rejects the calibration otherwise.
5. Run `PhCalibrator.fit()`. Accept only `CAL_OK`: spread at least 2 pH, slope magnitude 0.05-0.50 V/pH, residual at most 0.10 pH, temperature spread at most 5 C. [DESIGN]
6. Compare with the stored calibration (`driftOk`): slope change at most 10 % and offset shift at most 0.2 pH, otherwise report "probe ageing or contamination, replace or clean". [DESIGN]
7. Store the 20-byte blob (with CRC-16) in EEPROM together with the date; on boot, refuse to dose if the blob fails its CRC or is older than the recalibration interval.

**Recalibration interval:** before each experiment and at least monthly. [DESIGN, confirm from literature]

**Run-time conversion:** `phFromVoltage(cal, volts, DS18B20 water temperature)`.

**What the simulation says** (results/ph_calibration_study.md, assumed noise): the old tutorial constants give about 1.3 pH RMS error; a two-point calibration gives 0.03 pH; three points with temperature compensation give 0.02 pH. In the closed-loop simulation the old constants kept the true pH near 5.5 for the whole run; the calibrated probe kept it at 6.5-7.2.
