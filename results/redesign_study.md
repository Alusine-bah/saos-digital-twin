# Redesign study (7 days, 3 seeds, mean)

| Candidate | Targets | air<35C % | air max C | water 25-30C % | fan tog/day | blackout h | SoC min % | used Wh/d |
|---|---|---|---|---|---|---|---|---|
| v1 baseline | - | 57.7 | 38.8 | 28.8 | 156.5 | 0.0 | 26.7 | 168.9 |
| fan dwell 5 min on/off | R6 | 57.7 | 38.8 | 24.8 | 23.6 | 0.0 | 28.4 | 166.8 |
| fan dwell 10 min on/off | R6 | 57.7 | 38.8 | 20.6 | 17.2 | 0.0 | 29.5 | 165.5 |
| wider hysteresis 30/26 | R6 | 57.7 | 38.8 | 29.7 | 0.1 | 0.0 | 26.0 | 169.6 |
| hysteresis 30/26 + dwell 5 min | R6 | 57.7 | 38.8 | 29.7 | 0.1 | 0.0 | 26.0 | 169.6 |
| fan on at 28 / off 26 + dwell 5 min | R3 | 57.7 | 38.8 | 29.7 | 0.1 | 0.0 | 26.0 | 169.6 |
| bigger fan, 1.5 air changes/min | R3 | 63.4 | 38.0 | 33.3 | 56.3 | 0.0 | 31.6 | 162.9 |
| bigger fan 2.5 ach + dwell 5 min | R3 | 72.4 | 36.8 | 47.4 | 92.0 | 0.0 | 34.6 | 158.7 |
| shade net: solar gain 6 K + dwell | R3/R12 | 75.6 | 36.4 | 53.9 | 82.0 | 0.0 | 36.6 | 155.7 |
| cloudy: v1 100 W / 120 Wh | R5 | 57.7 | 38.8 | 28.8 | 156.5 | 27.6 | 0.0 | 168.9 |
| cloudy: 200 W panel | R5 | 57.7 | 38.8 | 28.8 | 156.5 | 0.0 | 24.9 | 168.9 |
| cloudy: 2x battery (240 Wh usable) | R5 | 57.7 | 38.8 | 28.8 | 156.5 | 11.4 | 0.0 | 168.9 |
| cloudy: 200 W + 240 Wh | R5 | 57.7 | 38.8 | 28.8 | 156.5 | 0.0 | 61.6 | 168.9 |
| cloudy: 150 W + 240 Wh | R5 | 57.7 | 38.8 | 28.8 | 156.5 | 0.0 | 61.3 | 168.9 |

Note: the energy figures use the assumed load list in config.py; fan wattage and the 29 C ambient are assumptions.
