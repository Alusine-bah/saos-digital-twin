# Stage 5 validation (7 days x 10 seeds per scenario)

Simulation-only. Requirements are our own [DESIGN] targets. Worst case over seeds decides pass/fail.

| ID | Requirement | Min | Mean | Max | Worst-case result | Verdict |
|---|---|---|---|---|---|---|
| R1 | pH inside the control band (+/-0.05) at least 95 % of the time | 100.0 | 100.0 | 100.0 | 100.0 >= 95 | PASS |
| R2 | pH recovers from a -0.9 shock: out-of-band time under 2 h | 53.0 | 53.2 | 54.0 | 54.0 <= 7200 | PASS |
| R3 | Air under 35 C at least 90 % of the time (outdoor, 29 C mean) | 63.1 | 63.1 | 63.1 | 63.1 >= 90 | FAIL |
| R4 | Battery never blacks out on an average-sun day | 0.0 | 0.0 | 0.0 | 0.0 <= 0 | PASS |
| R5 | Battery never blacks out under 30 % sun | 27.9 | 27.9 | 27.9 | 27.9 <= 0 | FAIL |
| R6 | Every relay switches at most 100 times per day (relay life) | 10.9 | 11.5 | 12.0 | 12.0 <= 100 | PASS |
| R7 | Tank level never below 35 % | 41.3 | 41.5 | 41.6 | 41.3 >= 35 | PASS |
| R8 | TDS inside 600-720 ppm at least 90 % of the time | 100.0 | 100.0 | 100.0 | 100.0 >= 90 | PASS |
| R9 | Telemetry delivery at least 99 % on a clean link | 100.0 | 100.0 | 100.0 | 100.0 >= 99 | PASS |
| R10 | Command response mean under 1000 ms | 56.7 | 56.7 | 56.7 | 56.7 <= 1000 | PASS |
| R11 | Indoor mode: air under 35 C at least 99 % of the time | 100.0 | 100.0 | 100.0 | 100.0 >= 99 | PASS |
| R12 | Water within the tilapia band 25-30 C at least 80 % of the time (outdoor) | 6.3 | 6.3 | 6.3 | 6.3 >= 80 | FAIL |

Baseline relay toggles per day (mean): fan 0.2, ph_up 0.0, ph_down 0.0, nutrient 11.5, light 0.0, tank_pump 0.3

Seeds change only sensor noise, so spread is small; scenario assumptions (ambient, sun, tank volume) dominate.


**9 of 12 requirements pass.**

A FAIL is a finding about the v1 design under the stated assumptions, not a bug in the simulator.
Assumed inputs that drive the results are listed in docs/LITERATURE.md and saos_sim/config.py.
