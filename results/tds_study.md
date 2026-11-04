# TDS study (7 days, 3 seeds, mean)

True TDS is the simulated water, not the sensor reading. 1.5 mS/cm lettuce target is about 750 ppm on the 0.5 scale the DFRobot code uses (960 ppm on the 0.64 scale).

| Case | nutrient toggles/day | true TDS mean | true TDS min | true TDS max |
|---|---|---|---|---|
| v1: 600/620 (20 ppm band) | 11.5 | 620.3 | 608.7 | 650.0 |
| v1 band + noise 30 ppm | 23.2 | 633.4 | 623.2 | 650.4 |
| band 600/650 | 4.4 | 633.9 | 608.8 | 663.4 |
| band 600/700 | 2.3 | 658.9 | 609.3 | 711.2 |
| band 600/700 + dwell 5 min | 2.3 | 658.9 | 609.3 | 711.2 |
| v1 band, sensor reads +100 ppm too high | 10.1 | 530.8 | 508.4 | 650.0 |
| v1 band, sensor reads -100 ppm too low | 12.3 | 719.4 | 650.0 | 734.3 |
| band 600/700, sensor +100 | 2.0 | 564.3 | 509.3 | 650.0 |
| band 600/700, sensor -100 | 2.3 | 761.1 | 650.0 | 813.6 |
