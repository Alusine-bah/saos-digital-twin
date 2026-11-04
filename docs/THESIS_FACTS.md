# Facts read from the thesis (2026-11-04), for the model

- Tank volume, fish count, feed rate, grow-bed size: NOT stated in the thesis. Still needed from the team.
- Prototype: vertical PVC/MDF rack, tilapia in the bottom tank, mint and lettuce in two grow beds above; indoor lab bench testing only.
- Power: 100 W panel, MPPT, 12 V 20 Ah lead-acid, 50 % DoD = 120 Wh usable; nominal 17.2 W (about 413 Wh/day), peak 26.9 W. Daily panel yield assumed 500 Wh (5 peak sun hours), a 21 % margin over 413 Wh.
- Pumps run at 3 V, fan at 5 V, stepped down from the 12 V bus; air pump 0.5 A, LED grow lights 12 W (3 tiers), heater 4.8 W, 11-channel relay bank.
- Measured in thesis: latency 2 ms mean (max 23.3 ms), PDR 93 %, response 0.029 s; the thesis says UART 115200 baud, but the recovered firmware uses 9600. Flag as a discrepancy.
- Thesis benchmarks cited: Wan [5] 99.2 % PDR at 90 m; Fathi [22] latency < 1.5 s; Alselek [7] cost GBP 3,800+.
- Budget BDT 15,000.

## Team answers (2026-11-04)
- Testing month: September (Dhaka mean ~29 C, high 32, low 26; weather2travel.com). amb_swing_c set 3.0.
- From photo [ESTIMATE]: plastic storage-box tank, about 25 L water; about 5-8 dark fish (6 used); two shallow grow trays about 35 x 25 cm. Feed amount and ambient not recorded.
