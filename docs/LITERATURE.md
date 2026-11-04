# Literature values used by the simulator

Retrieved 2026-11-04 by web search; please confirm each in Google Scholar before quoting in a paper.
Tags: [CITED] = number appears in the source; [DERIVED] = my calculation from cited numbers (assumptions listed);
[ASSUMED] = still no source.

## Topic 1: pH decline and base addition in aquaponics

| Value | Source | Used for |
|---|---|---|
| Nitrification consumes 7.14 g alkalinity (as CaCO3) per g ammonia-N oxidised (7.05 g from the overall stoichiometric equation); 4.57 g O2 per g TAN (4.18 g overall) [CITED] | Ebeling, J.M., *Recirculating Aquaculture Systems Short Course*, Aquaculture Systems Technologies (year not stated on the copy retrieved) | `alk_loss_from_feed()` |
| About 0.03 kg ammonia-N per kg feed; a table in the same document implies 50.4 g NH4-N per kg feed at 35 % protein (so 0.03-0.05) [CITED, the two figures disagree] | same | `tan_per_feed` |
| Rule of thumb: 0.25 kg sodium bicarbonate per kg feed [CITED] | same | cross-check: 0.25 kg NaHCO3 is about 0.15 kg alkalinity, close to the 0.21 kg/kg from 0.03 x 7.14 |
| UVI system (111,196 L): 22.5 kg Ca(OH)2 in 23 doses and 21.5 kg KOH in 22 doses over two basil trials; annual projection 40.65 kg Ca(OH)2 and 38.85 kg KOH [CITED] | Rakocy, Bailey, Shultz and Thoman, "Update on tilapia and vegetable production in the UVI aquaponic system" (ISTA6 proceedings; the page cites Rakocy, Shultz, Bailey and Thoman 2004, *Acta Horticulturae* 648:63-69) | net alkalinity loss |
| pH held at 7.0-7.5 by alternately adding Ca(OH)2 and KOH; pH checked daily; "nitrification produces acid and the pH decreased daily"; pH must stay above 7.0 for nitrification [CITED] | same | control target, dosing practice |
| Total alkalinity 65.6-206.7 mg/L as CaCO3 (means 88.6-115.9); pH means 7.1-7.4 [CITED] | same | `alk_ref_mgl` range |
| UVI plant growing area 214 m2; feed to area ratio 81.4 g/day/m2 (batch basil) and 99.6 g/day/m2 (staggered basil); four 7.8 m3 rearing tanks; fish stocked at 77-154 fish/m3, fingerlings 43-138 g, harvest about 814 g Nile tilapia; fed to satiation three times daily [CITED] | same | feed per volume, stocking |
| UVI total feed = ratio x area = 17.4-21.3 kg/day (assumes the whole 214 m2 is planted) [DERIVED]; gross alkalinity demand = 33.6-41.1 mg/L/day (0.03 kg TAN/kg feed x 7.14); net/gross = **5.4-6.6 %** (3.2 % if 0.05 kg TAN/kg feed) [DERIVED] | calculated here | `plant_offset` = 0.94 |
| Net alkalinity loss in the UVI system: (40.65 kg x 1.351 + 38.85 kg x 0.892) / 111,196 L / 365 d = **2.2 mg/L/day** [DERIVED; equivalents per gram: Ca(OH)2 2 eq/74.09 g, KOH 1 eq/56.11 g, 1 eq = 50.04 g as CaCO3] | calculated here | lower bound of `alk_loss_mgl_day` |
| Add base when pH falls below 6.0; calcium hydroxide, calcium carbonate, potassium hydroxide, potassium carbonate listed; "small additions result in a large increase in pH"; change pH slowly [CITED] | Hager, Bright, Dusci and Tidwell (2021), *Aquaponics Production Manual*, Kentucky State University, section 6.7; Somerville et al. (2014), FAO *Small-scale aquaponic food production* | alarm limit design, pulse dosing rationale |
| Potassium and mixed potassium-calcium buffers gave the best lettuce yield; no significant pH difference between buffers; 12 x 140 L units, Murray cod and lettuce [CITED] | Lennard, W.A. (2020), *Aquaculture and Fisheries* 6(5):495-505, doi 10.1016/j.aaf.2020.07.001 | choice of reagent for v2 |

## Topic 2: greenhouse temperature, ventilation and fan effectiveness

| Value | Source | Used for |
|---|---|---|
| Fan capacity should exchange 1.0-1.5 times the greenhouse air volume per minute; intake vents 1.25-1.5 times the exhaust fan area [CITED] | Pickens, J.M. and Danaher, J. (2016), *Controlling the Greenhouse Environment for Aquaponics*, SRAC Publication 5008, Southern Regional Aquaculture Center | `fan_vent_fraction_from_ach()` |
| "Generally accepted minimum ventilation rate for temperature control in the summer is one air change per minute"; winter 2-3 air changes per hour; higher ventilation reduces the inside-minus-outside temperature rise; shading is "very effective" (no numbers in the text) [CITED] | Watson, J.A., Gomez, C., Buffington, D.E., Bucklin, R., Henley, R.W. and McConnell, D. (2019), *Greenhouse Ventilation* (AE-10), UF/IFAS Extension, originally 1987 | cross-check of 1 air change per minute |
| Greenhouse time constant about 0.75 h (45 min) for a 217 m2 house; Albright et al. (1985) report about 40 min for dry greenhouses and 4-5 h for wet ones; overall heat transfer coefficient U = 5 + 1.2 v W/m2K (8.82 at 3.18 m/s wind); lumped two-node energy balance for air and thermal mass [CITED] | Janius, R.B. and Jenkins, B.M. (2004), "Determination of greenhouse time constant using steady-state assumption", *Pertanika J. Sci. & Technol.* 12(1):93-101 | `tau_air_s` range, U value |
| DHT11: temperature 0-50 C, accuracy +/-2 C, resolution 1 C; humidity 20-90 %RH, +/-5 %RH; minimum sampling interval 2 s [CITED] | Aosong Electronics, DHT11 datasheet | sensor model, `dht_bias_c` |
| Tilapia: optimal growth 25-30 C (best 28 C); appetite and growth fall below 20 C; feeding stops below 16 C; mortality possible below 12 C; best dissolved oxygen 5-8 mg/L in recirculating systems [CITED] | Ontario Ministry of Agriculture, Food and Rural Affairs (2023), *Species Profile for Aquaculture: Tilapia*, factsheet 23-093 | water temperature target (25-30 C) |

Derived (my calculation, assumptions in `config.py`):
* Heat balance: temperature rise above ambient = q / (UA + rho cp Q). With 0.7 x 800 W/m2 transmitted sunlight, U = 8.82, surface/volume 1.7 and a 3 m height the rise is 12.4 K without a fan and 5.3 K with 1 air change per minute, so the fan removes 57 % (67 % at 1.5 air changes per minute; 70-78 % if U = 5). Model default 0.60.
* A fan that removes a share f of the rise also shortens the air time constant to (1 - f) of its value.

## Observation about the prototype itself (needs your confirmation)
The thesis (section 5.2) says the two small fans are "mounted at the top of the electronics compartment to protect the relay bank and the power electronics". The firmware calls the same relay an exhaust fan and switches it on the DHT11 reading (30 C on, 28 C off). Which space does the DHT11 measure: the grow area or the electronics box? The answer decides whether the greenhouse heat-balance model applies or an enclosure model with the electronics' own heat (the 17-27 W load) is needed.

## Topic 3: water loss (evaporation and transpiration)

| Value | Source | Used for |
|---|---|---|
| Daily make-up water averaged 2.61 m3 = 2.4 % of system volume (111,196 L); average daily exchange 0.26-0.46 % of volume; loss "attributed to sludge removal, net filter washing, splashing, evaporation and transpiration" (no separate evaporation/transpiration figures) [CITED] | Rakocy et al., UVI system, ISTA6 proceedings (pdf 676) | order of magnitude, 2.4 % of volume per day |
| UVI-type aquaponic system "requires a daily water addition of 1-1.5 percent of the total system's volume" (435 gal/day at 1.5 %); RAS in general under 1 % exchange [CITED, secondary] | Food & Water Watch fact sheet (Aug 2009), citing Rakocy (2009) and Torsten et al. (2009); not peer reviewed | lower bound 1-1.5 % |
| Pan evaporation about 3.7 mm/day (equatorial zone: Bangui, Brazzaville; monthly 3.0-4.6) and about 7.0 mm/day (dry zone: Ndjamena; monthly 4.9-8.9); pan coefficient PET/E 0.92 equatorial, 0.73 dry [CITED pan coefficient; the mm/day values are DERIVED by me as PET / pan coefficient from the paper's tables] | Riou, C. (1984), "Experimental study of potential evapotranspiration (PET) in Central Africa", *J. Hydrology* 72:275-288 | surface evaporation, 3.7-7 mm/day |
| Hydroponic lettuce in a planthouse, 40 days: yield 1114.6 g/m2, water productivity 29.58 g/L, Kc from 0.7 down to 0.4 and up to 1.4 [CITED]; consumptive use = 1114.6 / 29.58 = 37.7 L/m2 over 40 days = about 0.94 L/m2/day [DERIVED] | Muharomah, Setiawan, Purwanto, Liyantono (2020), *CIGR Journal* 22(1) | plant transpiration, about 1 mm/day |

Not found: a Bangladesh evaporation figure in mm/day (the Mymensingh paper by Mahmud et al. 2020, *J. Bangladesh Agric. Univ.* 18(3):742-750, may contain tables; check the full text).

Derived for the prototype [ESTIMATE]: about 5 mm/day total (surface plus plants, assuming plant area similar to tank area). The firmware level scale is 12 cm, so 1 % = 1.2 mm and the loss is about 4 % of the scale per day = **0.17 %/h** (range 0.11-0.30). The earlier model value 0.9 %/h was an unsupported guess about 5x too high. Cross-check: 0.6-1.2 L/day from a 14-29 L tank = 1.7-3.4 % of a 35 L system, consistent with UVI 2.4 % and 1-1.5 %.

## Topic 4: TDS / EC ranges, sensor accuracy and nutrient control

| Value | Source | Used for |
|---|---|---|
| DFRobot Gravity analog TDS sensor SEN0244: range 0-1000 ppm, **accuracy +/-10 % of full scale at 25 C (about +/-100 ppm)**, output 0-2.3 V, supply 3.3-5.5 V; no temperature sensor on the probe (default 25 C unless one is added) [CITED] | DFRobot wiki, SEN0244 | sensor error, `tds_bias_ppm` |
| Leafy-green hydroponic recipe: EC 1.5 mS/cm, pH 5.6; half strength for the first two weeks; relation "TDS / 640 = EC (mS/cm)" (tomato recipes 1.5, 1.9, 2.2) [CITED] | Hooks, UA-CEAC, 2026 Greenhouse Hydroponic Tomato Workshop, Module 3 (University of Arizona) | target EC for lettuce |
| Aquaponic and hydroponic lettuce/basil trial with Nile tilapia: EC kept at 1.5 mS/cm by adjusting feeding rate; EC "kept above 1.5 mS/cm for plant growth" (citing earlier studies); EC rose over time in the aquaponic system from accumulating nutrients; pH 5-8 acceptable for Nile tilapia; 26-28 C, 20 kg/m3 [CITED] | Wang, Yang and Kim (2023), "pH dynamics in aquaponic systems: implications for plant and fish crop productivity and yield", *Sustainability* 15(9):7137 | EC target, EC drift direction |
| Egyptian tilapia and lettuce system: aquaponic EC 671-826 (reported in "mg/L", units doubtful); hydroponic reference solution adjusted to EC 800-840 ppm at pH 6.0-6.5; solution N 210, P 31, K 234, Ca 200, Mg 48 ppm [CITED, authors and title not shown on the page I could read; Benha University, 2022 trial] | Springer *Scientific Reports* 2024, article s41598-024-54656-y | order of magnitude |
| 1 ppm TDS = 2 uS/cm (the 0.5 scale); nitrate target for aquaponics 50-150 ppm; most fish tolerate nitrate above 400 mg/L; alkalinity 50-200 ppm, 100 ideal [CITED, a presentation without year or publisher, treat as weak] | Klinger-Bowen, University of Hawaii (undated slides) | scale factor, context |

Interpretation [DERIVED]:
* The DFRobot code multiplies by 0.5, so the firmware's 600 ppm is about 1.2 mS/cm and 620 ppm about 1.24 mS/cm. That is below the 1.5 mS/cm lettuce recipe (750 ppm on the 0.5 scale; 960 ppm on the 0.64 scale), which is plausible for aquaponics where fish waste supplies part of the nutrients, but it is a design choice with no source in the thesis. Needs a plant-side check.
* **The firmware's 20 ppm hysteresis is one fifth of the sensor's stated accuracy (+/-100 ppm)** and comparable to the filtered noise, so the band is not meaningful and chatters when noise grows.
* Not found: a measured plant nutrient uptake rate in ppm per hour. `tds_rise_per_h`, `tds_uptake_per_h` and `tds_dose_per_s` stay [ASSUMED]. Wang et al. say EC tends to rise in aquaponics (net accumulation), while the model currently has a net decline of 5 ppm/h that dosing offsets: unverified.

## Topic 5: power draw, solar yield and battery depth of discharge

| Value | Source | Used for |
|---|---|---|
| ESP32 (ESP-WROOM-32): Wi-Fi TX 160-260 mA, Wi-Fi/BT RX and listening 80-90 mA, modem-sleep 3-20 mA, light-sleep 0.8 mA; module average operating current 80 mA; supply 3.3 V typical [CITED] | Espressif ESP-WROOM-32 datasheet, Table 5 | ESP32 average about 0.27 W (80 mA x 3.3 V), peak about 0.86 W [DERIVED] |
| 5 V SRD-05VDC-SL-C relay: coil 360 mW (about 71.4 mA); contacts 10-15 A at 250 V AC depending on variant [CITED] | Songle SRD-05VDC-SL-C listing (LCSC) | `p_relay_coil_w` 0.36 W per ON relay (added to the model; v1 model ignored it) |
| 12 V peristaltic dosing pump: 0.4 A, 5 W, 19-100 mL/min, silicone tube 3x5 mm [CITED, one product listing, not necessarily the prototype's pump] | Robu.in product page | upper estimate for pH and nutrient pump power |
| Solar PV output per installed kW (NASA POWER hourly data, profileSOLAR analysis): Freetown seasons 4.58 (summer, lowest), 5.65, 5.77, 6.16 (spring, highest) kWh/kW/day; Savar, Bangladesh 4.01 (winter, lowest), 4.53 (summer), 4.72, 5.98 (spring, highest) kWh/kW/day [CITED, seasonal averages only, not monthly; website analysis] | profileSOLAR, Freetown and Savar pages (2025) | model clear-day yield 4.25 kWh/kW/day = 5 peak sun hours x 0.85 sits at the low end of both ranges, so it is conservative |
| Lead-acid: deep-cycle designed for 50 % daily discharge; can be discharged up to 80 % without damage but this "shorten[s] the cycle-life"; shallow-cycle about 15 % daily, 50 % maximum; above 25 C capacity rises and life falls, about 50 % shorter life per 10 C (18 F) above 25 C; 20-25 % less capacity at 0 C [CITED] | Morningstar Corporation, "Primary design factors for lead acid batteries" (tech tip) | 50 % DoD assumption, hot-climate life warning |

Not found: a measured current for the Mega 2560 board, LCD and sensors, the prototype's pump and fan models, monthly (rather than seasonal) irradiation for a specific site, and a cycle-life-versus-DoD table.
Derived [DERIVED]: base load by components is about 0.5 W (Mega, assumed) + 0.27 W (ESP32 average) + 1 W (LCD, sensors, assumed) + converter loss 15 % = about 2.2 W, about half of the 4.2 W kept in the model; the 4.2 W figure came from earlier work and cannot be checked. A 12 V / 20 Ah battery is 240 Wh nominal, 120 Wh at 50 % DoD (thesis figure).
Findings (results/power_study.md): with a constant sun factor, the v1 100 W panel and 120 Wh usable battery cope down to 45 % of clear-day sun and fail at 30 % (27.6 h of blackout in 7 days). Break-even is about 0.38 (169 Wh/day used / 446 Wh/day at full sun). Halving the base load to 2.2 W removes the 30 % blackout; a 200 W panel, or 150 W with 240 Wh, also does. Allowing 80 % DoD (192 Wh) still blacks out for 18 h and shortens battery life. A constant 30 % sun for 7 days is a stress test and not a forecast.

## Topic 6: UART timing on the Mega 2560 and ESP32

| Value | Source | Used for |
|---|---|---|
| Arduino AVR core: `SERIAL_TX_BUFFER_SIZE` and `SERIAL_RX_BUFFER_SIZE` are 64 bytes when RAM span is 1023 bytes or more (16 bytes on smaller chips) [CITED, code] | arduino/ArduinoCore-avr, `HardwareSerial.h` | TX stall of a 205-byte frame = (205 - 64) x byte time; RX overrun limit |
| ESP32 Arduino core: default UART RX buffer 256 bytes, `setRxBufferSize()` must exceed the hardware FIFO length (`SOC_UART_FIFO_LEN`; the 128-byte value is not confirmed by the page I read) [CITED] | espressif/arduino-esp32 pull request 5583 | ESP32 side has more headroom than the Mega |
| AVR USART error tolerance, D = 8 data bits: normal speed Rslow 95.36 %, Rfast 104.58 %, max total error -4.54/+4.58 %, recommended receiver error +/-2.0 %; double speed -4.00/+3.90 %, recommended +/-1.5 % [CITED] | Microchip online documentation, USART "Error Tolerance" section | baud choice |
| Baud errors at 16 MHz with the Arduino U2X choice: 9600 +0.16 %, 38400 +0.16 %, 57600 -0.79 %, 115200 +2.12 % [DERIVED by me from the AVR formula UBRR = (F_CPU/4/baud - 1)/2; check on the board] | calculated here | results/uart_timing.md |
| ESP32 Wi-Fi/UART power, see topic 5 | - | - |

Not found: a measured latency of `Serial2` on the Mega or the ESP32 (these must be measured: test T1-T3 in docs/HARDWARE_TEST_PLAN.md); ESP32 UART baud error (it uses a fractional divider, so assumed negligible).
Findings: (1) the 147 ms/s TX stall of v1 follows directly from the 64-byte buffer; (2) 115200 on a 16 MHz Mega has little tolerance margin, so v2 should use 57600; (3) command bursts are the only receive-overrun risk, so the gateway paces frames 20 ms apart and the sketch's `pulseIn` timeout was cut to 4 ms. See results/uart_timing.md.

## Model built from these numbers
At constant dissolved CO2 the carbonate system gives pH = pH_ref + log10(Alk / Alk_ref) (Henderson-Hasselbalch; my derivation, assumes alkalinity is mostly bicarbonate near pH 7 and CO2 stays constant, which ignores fish respiration and plant CO2 uptake).
Consequences: the same dose moves pH more when alkalinity is low, and the pH controller's workload depends mostly on alkalinity and on how much of the nitrification acid the plants offset (results/ph_drift_sensitivity.md).

## Prototype estimate (made by me; the thesis gives none of these)
| Quantity | Estimate | Basis |
|---|---|---|
| Fish tank | 14-29 L (water column 12 cm; firmware `TANK_HEIGHT` 12.0 cm) | 12 cm x a 40x30 to 60x40 cm shelf footprint [ESTIMATE] |
| Whole circulating volume | 20-50 L, central 35 L | tank + grow-bed reservoir + pipes [ESTIMATE] |
| Fish | about 3-5 juvenile tilapia, 0.15-0.45 kg total | UVI stocking 77-154 fish/m3 at 43-138 g gives roughly 6-15 kg/m3 in the early growth stage [DERIVED] |
| Feed | 4-12 g/day, central 8 g | about 3 % of body weight per day, a general rule of thumb [ASSUMED, not cited] |
| Gross alkalinity loss | 17 / 49 / 129 mg/L/day (feed 4 g in 50 L / 8 g in 35 L / 12 g in 20 L) | 0.03 x 7.14 x feed / volume [DERIVED] |
| Net alkalinity loss | **1.0 / 2.9 / 7.7 mg/L/day** | gross x (1 - 0.94) [DERIVED from the UVI net/gross ratio, which may not transfer to a 35 L system] |

At 100 mg/L alkalinity a net loss of 2.9 mg/L/day lowers pH by only about 0.013 per day, so the pH controller would rarely act. This agrees with the thesis dashboard showing a steady pH of 7.12, but that is a consistency check, not a validation.

## Still needed from you (cannot be found in the literature)
If you remember them, the real tank volume, fish count and daily feed replace the estimates above. The most valuable measurement is the water's alkalinity (a cheap KH test kit): it sets how fast pH reacts. `alk_loss_from_feed(feed_g_per_day, volume_l, plant_offset=0.94)` then gives the net loss.

## Topic 7: Bangladesh evaporation (checked 2026-11-04)

- [CITED] Amirulhussain, M. (1986). Evaporation over Bangladesh. MAUSAM 37(3), 373-376. Five years of Class-A pan data, 19 stations. Highest mean monthly 93.2 mm (April); mean annual 1142-1636 mm in the north-west and south-east; lowest annual 700 mm (Sylhet); December minimum 40-60 mm/month.
- [DERIVED] Annual range 1142-1636 mm = 3.1-4.5 mm/day pan; Sylhet 700 mm = 1.9 mm/day. A pan over-reads open water (pan coefficient commonly ~0.7), so open-tank evaporation is about 2-3 mm/day.
- Consequence: our 0.17 %/h level loss (about 5 mm/day) is plausible once plant transpiration is added to evaporation, but it is not separately validated. Keep as [DERIVED], flagged.
- Caveat: 1986 data, pan not tank. Abstract only (full text not read).

## Topic 8: Nutrient uptake and battery life (status)

- Nutrient uptake per day: NOT found. Inoue et al. 2025 (Agriculture 15(13), 1350; preprint 202505.0793) report only mean tank EC set-points (about 0.5-3.1 dS/m), not daily rates. Keep TDS drift as [ESTIMATE].
- Lead-acid cycle life vs depth of discharge: only forum/blog hits found. Keep 50 % DoD as [ASSUMED]; need a manufacturer datasheet (cycle-life curve) for the actual battery.
- Related work candidate: Wan et al. 2022, modularized IoT aquaponics with edge computing (PMC9739085). Page blocked by CAPTCHA, not read. Do not cite until verified.
