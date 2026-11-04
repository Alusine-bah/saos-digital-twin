# pH calibration study (Monte Carlo, 4000 calibrations)

Probe truth = the project's own two-point buffer data. Voltage noise 2 mV, buffer tolerance 0.02 pH (assumed).

| Method | RMS error over pH 5-9, all temps | RMS error in control band 6.5-7.2, 25 C | Worst mean error, any pH/temp |
|---|---|---|---|
| v1 tutorial constants (no calibration) | 1.351 | 1.298 | 1.85 |
| 2-point (4.01/6.86), no temp comp | 0.037 | 0.025 | 0.07 |
| 2-point + temperature comp | 0.028 | 0.025 | 0.00 |
| 3-point (4.01/6.86/9.18) + temp comp | 0.017 | 0.016 | 0.00 |

C++ `saos_calib` vs numpy `polyfit` on 50 random calibrations: max difference 4.94e-12 (slope and v7).

