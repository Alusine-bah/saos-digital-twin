"""How the tank-pump workload and tank level depend on the water loss rate (%/h of the 12 cm level scale)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from saos_sim.config import Params
from saos_sim.sim import run, with_
rows = ["# Water-loss sensitivity (7 days)", "", "| Loss %/h | mm/day | Source / meaning | Tank pump starts/day | Level min % | Level ok % |", "|---|---|---|---|---|---|"]
for lab, v in [("0.11", "1.5 % of 35 L system/day (low)"), ("0.17", "central estimate, 5 mm/day"), ("0.30", "dry-zone evaporation 7 mm/day + plants"), ("0.90", "old assumed value")]:
    r, _ = run(with_(Params(days=7.0), level_loss_per_h=float(lab)), log_every=3600)
    rows.append(f"| {lab} | {float(lab) * 1.2 * 24:.1f} | {v} | {r['toggles_tank_pump_day'] / 2:.1f} | {r['level_min_pct']:.1f} | {r['level_ok_pct']:.1f} |")
open(os.path.join(os.path.dirname(__file__), "..", "results", "water_loss_sensitivity.md"), "w").write("\n".join(rows) + "\n")
print("\n".join(rows))
