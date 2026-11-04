"""TDS control: hysteresis width, sensor noise and the +/-100 ppm sensor accuracy.  Fields: true TDS inside plant-useful range."""
import os, sys, statistics as st
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from saos_sim.config import Params
from saos_sim.sim import run, with_
base = Params(days=7.0)
C = [("v1: 600/620 (20 ppm band)", base), ("v1 band + noise 30 ppm", with_(base, tds_noise=30.0)),
     ("band 600/650", with_(base, tds_high=650.0)), ("band 600/700", with_(base, tds_high=700.0)),
     ("band 600/700 + dwell 5 min", with_(base, tds_high=700.0, min_on_s=300, min_off_s=300)),
     ("v1 band, sensor reads +100 ppm too high", with_(base, tds_bias_ppm=100.0)),
     ("v1 band, sensor reads -100 ppm too low", with_(base, tds_bias_ppm=-100.0)),
     ("band 600/700, sensor +100", with_(base, tds_high=700.0, tds_bias_ppm=100.0)),
     ("band 600/700, sensor -100", with_(base, tds_high=700.0, tds_bias_ppm=-100.0))]
lines = ["# TDS study (7 days, 3 seeds, mean)", "", "True TDS is the simulated water, not the sensor reading. 1.5 mS/cm lettuce target is about 750 ppm on the 0.5 scale the DFRobot code uses (960 ppm on the 0.64 scale).", "",
         "| Case | nutrient toggles/day | true TDS mean | true TDS min | true TDS max |", "|---|---|---|---|---|"]
for lab, p in C:
    rs = []
    for sd in (1, 2, 3):
        rows = run(with_(p, seed=sd), log_every=60)[1]
        r = run(with_(p, seed=sd), log_every=3600)[0]
        t = [x["tds"] for x in rows]
        rs.append((r["toggles_nutrient_day"], st.mean(t), min(t), max(t)))
    lines.append(f"| {lab} | " + " | ".join(f"{st.mean(x[i] for x in rs):.1f}" for i in range(4)) + " |")
    print(lines[-1], flush=True)
open(os.path.join(os.path.dirname(__file__), "..", "results", "tds_study.md"), "w").write("\n".join(lines) + "\n")
