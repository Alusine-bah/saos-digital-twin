"""Stage 5b: do candidate redesigns fix the v1 validation failures? (R3 air, R5 cloudy battery, R6 fan wear, R12 water band)
Each row changes one thing against the v1 baseline. All inputs are the same assumptions as run_validation.py."""
import os, sys, statistics as st
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from saos_sim.config import Params, fan_vent_fraction_from_ach
from saos_sim.sim import run, with_

base = Params(days=7.0)
cloudy = with_(base, cloud_factor=0.3)
C = [  # (label, params, what it targets)
    ("v1 baseline", base, "-"),
    ("fan dwell 5 min on/off", with_(base, min_on_s=300, min_off_s=300), "R6"),
    ("fan dwell 10 min on/off", with_(base, min_on_s=600, min_off_s=600), "R6"),
    ("wider hysteresis 30/26", with_(base, fan_off_c=26.0), "R6"),
    ("hysteresis 30/26 + dwell 5 min", with_(base, fan_off_c=26.0, min_on_s=300, min_off_s=300), "R6"),
    ("fan on at 28 / off 26 + dwell 5 min", with_(base, fan_on_c=28.0, fan_off_c=26.0, min_on_s=300, min_off_s=300), "R3"),
    ("bigger fan, 1.5 air changes/min", with_(base, fan_vent_fraction=round(fan_vent_fraction_from_ach(1.5), 2), min_on_s=300, min_off_s=300), "R3"),
    ("bigger fan 2.5 ach + dwell 5 min", with_(base, fan_vent_fraction=round(fan_vent_fraction_from_ach(2.5), 2), min_on_s=300, min_off_s=300), "R3"),
    ("shade net: solar gain 6 K + dwell", with_(base, solar_gain_c=6.0, min_on_s=300, min_off_s=300), "R3/R12"),
    ("cloudy: v1 100 W / 120 Wh", cloudy, "R5"),
    ("cloudy: 200 W panel", with_(cloudy, panel_w=200.0), "R5"),
    ("cloudy: 2x battery (240 Wh usable)", with_(cloudy, battery_wh_usable=240.0), "R5"),
    ("cloudy: 200 W + 240 Wh", with_(cloudy, panel_w=200.0, battery_wh_usable=240.0), "R5"),
    ("cloudy: 150 W + 240 Wh", with_(cloudy, panel_w=150.0, battery_wh_usable=240.0), "R5"),
]
cols = [("air_below_35c_pct", "air<35C %"), ("air_max_c", "air max C"), ("water_25_30_pct", "water 25-30C %"),
        ("toggles_fan_day", "fan tog/day"), ("blackout_h", "blackout h"), ("soc_min_pct", "SoC min %"), ("energy_used_wh_day", "used Wh/d")]
lines = ["# Redesign study (7 days, 3 seeds, mean)", "", "| Candidate | Targets | " + " | ".join(c[1] for c in cols) + " |", "|---|---|" + "---|" * len(cols)]
for lab, p, tgt in C:
    rs = [run(with_(p, seed=s), log_every=3600)[0] for s in (1, 2, 3)]
    lines.append(f"| {lab} | {tgt} | " + " | ".join(f"{st.mean(r[k] for r in rs):.1f}" for k, _ in cols) + " |")
    print(lines[-1], flush=True)
lines += ["", "Note: the energy figures use the assumed load list in config.py; fan wattage and the 29 C ambient are assumptions."]
open(os.path.join(os.path.dirname(__file__), "..", "results", "redesign_study.md"), "w").write("\n".join(lines) + "\n")
