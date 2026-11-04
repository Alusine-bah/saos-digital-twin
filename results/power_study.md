# Power study (7 days, constant sun factor)

Model clear-day yield = peak_sun_hours 5.0 x charge_eff 0.85 = 4.25 kWh per kW per day. Cited seasonal PV output (NASA POWER via profileSOLAR): Freetown 4.58-6.16, Savar (Dhaka area) 4.01-5.98 kWh/kW/day, so the model sits at the low end of both.

| Case | Sun factor | Used Wh/day | Solar Wh/day | Blackout h in 7 d | SoC min % |
|---|---|---|---|---|---|
| v1: 100 W, 120 Wh usable | 1.00 | 169 | 446 | 0.0 | 27 |
| v1: 100 W, 120 Wh usable | 0.85 | 169 | 379 | 0.0 | 26 |
| v1: 100 W, 120 Wh usable | 0.60 | 169 | 267 | 0.0 | 25 |
| v1: 100 W, 120 Wh usable | 0.45 | 169 | 201 | 0.0 | 23 |
| v1: 100 W, 120 Wh usable | 0.30 | 169 | 134 | 27.6 | 0 |
| base load 2.2 W (component sum) | 0.60 | 121 | 267 | 0.0 | 47 |
| 200 W panel | 0.60 | 169 | 535 | 0.0 | 27 |
| 150 W + 240 Wh usable | 0.60 | 169 | 401 | 0.0 | 62 |
| base load 2.2 W (component sum) | 0.45 | 121 | 201 | 0.0 | 46 |
| 200 W panel | 0.45 | 169 | 401 | 0.0 | 26 |
| 150 W + 240 Wh usable | 0.45 | 169 | 301 | 0.0 | 62 |
| base load 2.2 W (component sum) | 0.30 | 121 | 134 | 0.0 | 45 |
| 200 W panel | 0.30 | 169 | 267 | 0.0 | 25 |
| 150 W + 240 Wh usable | 0.30 | 169 | 201 | 0.0 | 61 |
| relay coils off (v1 model before this topic) | 1.00 | 160 | 446 | 0.0 | 31 |
| DoD 80 % (192 Wh usable, shorter battery life) | 0.30 | 169 | 134 | 18.3 | 0 |
