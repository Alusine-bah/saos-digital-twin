# Redesign study (7 days, 3 seeds, mean)

| Candidate | Targets | air<35C % | air max C | water 25-30C % | fan tog/day | blackout h | SoC min % | used Wh/d |
|---|---|---|---|---|---|---|---|---|
| v1 baseline | - | 63.1 | 36.8 | 6.3 | 0.1 | 0.0 | 26.0 | 169.6 |
| fan dwell 5 min on/off | R6 | 63.1 | 36.8 | 6.3 | 0.1 | 0.0 | 26.0 | 169.6 |
| fan dwell 10 min on/off | R6 | 63.1 | 36.8 | 6.3 | 0.1 | 0.0 | 26.0 | 169.6 |
| wider hysteresis 30/26 | R6 | 63.1 | 36.8 | 6.3 | 0.1 | 0.0 | 26.0 | 169.6 |
| hysteresis 30/26 + dwell 5 min | R6 | 63.1 | 36.8 | 6.3 | 0.1 | 0.0 | 26.0 | 169.6 |
| fan on at 28 / off 26 + dwell 5 min | R3 | 63.1 | 36.8 | 6.3 | 0.1 | 0.0 | 26.0 | 169.6 |
| bigger fan, 1.5 air changes/min | R3 | 73.8 | 36.0 | 32.7 | 0.1 | 0.0 | 26.0 | 169.6 |
| bigger fan 2.5 ach + dwell 5 min | R3 | 100.0 | 34.8 | 53.3 | 42.1 | 0.0 | 30.3 | 164.6 |
| shade net: solar gain 6 K + dwell | R3/R12 | 100.0 | 34.4 | 60.9 | 59.7 | 0.0 | 31.9 | 162.5 |
| cloudy: v1 100 W / 120 Wh | R5 | 63.1 | 36.8 | 6.3 | 0.1 | 27.9 | 0.0 | 169.6 |
| cloudy: 200 W panel | R5 | 63.1 | 36.8 | 6.3 | 0.1 | 0.0 | 24.3 | 169.6 |
| cloudy: 2x battery (240 Wh usable) | R5 | 63.1 | 36.8 | 6.3 | 0.1 | 11.9 | 0.0 | 169.6 |
| cloudy: 200 W + 240 Wh | R5 | 63.1 | 36.8 | 6.3 | 0.1 | 0.0 | 61.3 | 169.6 |
| cloudy: 150 W + 240 Wh | R5 | 63.1 | 36.8 | 6.3 | 0.1 | 0.0 | 61.0 | 169.6 |

Note: the energy figures use the assumed load list in config.py; fan wattage and the 29 C ambient are assumptions.
