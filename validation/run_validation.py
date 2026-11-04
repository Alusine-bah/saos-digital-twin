"""Stage 5: requirement-based validation of the digital twin (simulation only, not hardware).

Each requirement is a [DESIGN] target chosen by us (not from the thesis) so the next prototype has a pass/fail
benchmark. Monte Carlo over noise seeds gives mean and worst case, not a single lucky run.
Usage: python validation/run_validation.py [days] [seeds]
"""
import os, sys, statistics as st
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from saos_sim.config import Params
from saos_sim.sim import run, with_

DAYS = float(sys.argv[1]) if len(sys.argv) > 1 else 7.0
SEEDS = range(1, (int(sys.argv[2]) if len(sys.argv) > 2 else 10) + 1)
OUT = os.path.join(os.path.dirname(__file__), "..", "results")

# (id, description, scenario-name, metric key, comparator, threshold, use worst-case over seeds)
REQ = [
    ("R1", "pH inside the control band (+/-0.05) at least 95 % of the time", "baseline", "ph_in_band_pct", ">=", 95.0),
    ("R2", "pH recovers from a -0.9 shock: out-of-band time under 2 h", "ph_shock", "ph_out_of_band_s", "<=", 7200.0),
    ("R3", "Air under 35 C at least 90 % of the time (outdoor, 29 C mean)", "baseline", "air_below_35c_pct", ">=", 90.0),
    ("R4", "Battery never blacks out on an average-sun day", "baseline", "blackout_h", "<=", 0.0),
    ("R5", "Battery never blacks out under 30 % sun", "cloudy", "blackout_h", "<=", 0.0),
    ("R6", "Every relay switches at most 100 times per day (relay life)", "baseline", "max_toggles_day", "<=", 100.0),
    ("R7", "Tank level never below 35 %", "baseline", "level_min_pct", ">=", 35.0),
    ("R8", "TDS inside 600-720 ppm at least 90 % of the time", "baseline", "tds_in_band_pct", ">=", 90.0),
    ("R9", "Telemetry delivery at least 99 % on a clean link", "baseline", "pdr_pct", ">=", 99.0),
    ("R10", "Command response mean under 1000 ms", "override", "resp_mean_ms", "<=", 1000.0),
    ("R11", "Indoor mode: air under 35 C at least 99 % of the time", "indoor", "air_below_35c_pct", ">=", 99.0),
    ("R12", "Water within the tilapia band 25-30 C at least 80 % of the time (outdoor)", "baseline", "water_25_30_pct", ">=", 80.0),
]

base = Params(days=DAYS)
SCEN = {
    "baseline": base,
    "cloudy": with_(base, cloud_factor=0.3),
    "ph_shock": with_(base, ph_shock_h=10.0, ph_shock_delta=-0.9),
    "indoor": with_(base, solar_gain_c=1.5, amb_swing_c=2.0, amb_mean_c=28.0),
    "override": base,      # operator forces the fan off for 3 h on day 2 through the link
}
OVERRIDES = {"override": [(30 * 3600, 33 * 3600, "fan", False)]}

data = {}
for name, p in SCEN.items():
    runs = []
    for s in SEEDS:
        r, _ = run(with_(p, seed=s), esp_overrides=OVERRIDES.get(name), log_every=3600)
        r["max_toggles_day"] = max(v for k, v in r.items() if k.startswith("toggles_") and k.endswith("_day"))
        runs.append(r)
    data[name] = runs
    print("done", name, flush=True)

def agg(name, key):
    v = [r[key] for r in data[name]]
    return min(v), st.mean(v), max(v)

lines = [f"# Stage 5 validation ({DAYS:g} days x {len(list(SEEDS))} seeds per scenario)", "",
         "Simulation-only. Requirements are our own [DESIGN] targets. Worst case over seeds decides pass/fail.", "",
         "| ID | Requirement | Min | Mean | Max | Worst-case result | Verdict |", "|---|---|---|---|---|---|---|"]
npass = 0
for rid, desc, sc, key, op, thr in REQ:
    lo, mean, hi = agg(sc, key)
    worst = lo if op == ">=" else hi
    ok = worst >= thr if op == ">=" else worst <= thr
    npass += ok
    lines.append(f"| {rid} | {desc} | {lo:.1f} | {mean:.1f} | {hi:.1f} | {worst:.1f} {op} {thr:g} | {'PASS' if ok else 'FAIL'} |")
tg = {k: round(st.mean(r[k] for r in data["baseline"]), 1) for k in data["baseline"][0] if k.startswith("toggles_") and k.endswith("_day")}
lines += ["", "Baseline relay toggles per day (mean): " + ", ".join(f"{k[8:-4]} {v}" for k, v in tg.items()), "",
          "Seeds change only sensor noise, so spread is small; scenario assumptions (ambient, sun, tank volume) dominate.", ""]
lines += ["", f"**{npass} of {len(REQ)} requirements pass.**", "",
          "A FAIL is a finding about the v1 design under the stated assumptions, not a bug in the simulator.",
          "Assumed inputs that drive the results are listed in docs/LITERATURE.md and saos_sim/config.py."]
open(os.path.join(OUT, "validation.md"), "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
