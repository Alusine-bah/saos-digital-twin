"""Run the benchmark scenarios -> results/*.csv, summary.md, plots."""
import json
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from saos_sim.config import Params
from saos_sim.sim import run, with_
from saos_sim.link import build_frame, serialization_ms

OUT = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(OUT, exist_ok=True)
base = Params(days=4.0)

SCENARIOS = {
    "S1_baseline":        (base, None),
    "S2_heatwave_+6C":    (with_(base, heatwave_c=6.0), None),
    "S3_cloudy_30pct":    (with_(base, cloud_factor=0.3), None),
    "S4_pH_pulse_dosing": (with_(base, ph_strategy="pulse"), None),
    "S5_thesis_link_7pct_loss": (with_(base, frame_loss=0.07), None),
    # dashboard forces the fan OFF for 3 h at midday on day 2 (AUTO suspended, then watchdog)
    "S7_pH_shock_continuous": (with_(base, ph_shock_h=10.0, ph_shock_delta=-0.9), None),
    "S8_pH_shock_pulse": (with_(base, ph_shock_h=10.0, ph_shock_delta=-0.9, ph_strategy="pulse"), None),
    "S9_dht11_bias_+2C": (with_(base, dht_bias_c=2.0), None),
    "S10_ph_probe_calibration_mismatch": (with_(base, ph_cal_gain=1.222, ph_cal_offset=-0.233, days=4.0), None),
    # indoor mode [ESTIMATE]: no sun, heat only from light+electronics, steadier room temperature
    "S11_indoor_mode": (with_(base, solar_gain_c=1.5, amb_swing_c=2.0, amb_mean_c=28.0), None),
    "S6_esp_override_fan_off": (base, [(30 * 3600, 33 * 3600, "fan", False)]),
}

results = {}
series = {}
for name, (p, ov) in SCENARIOS.items():
    res, rows = run(p, esp_overrides=ov, csv_path=os.path.join(OUT, f"{name}.csv"))
    results[name] = res
    series[name] = rows
    print(f"{name}: pH in band {res['ph_in_band_pct']:.1f}%  air max {res['air_max_c']:.1f}C  "
          f"SoC min {res['soc_min_pct']:.0f}%  PDR {res['pdr_pct']:.1f}%")

# ---- link physics at different baud rates -------------------------------
frame_len = int(results["S1_baseline"]["frame_bytes_mean"])
baud_tbl = {b: serialization_ms(frame_len, b) for b in (9600, 57600, 115200)}
results["_frame_bytes"] = frame_len
results["_serialization_ms_by_baud"] = baud_tbl
with open(os.path.join(OUT, "results.json"), "w") as f:
    json.dump(results, f, indent=2)

# ---- summary table ------------------------------------------------------
cols = [("ph_in_band_pct", "pH in band %"), ("ph_true_min", "true pH min"), ("air_max_c", "Air max C"), ("tds_in_band_pct", "TDS 600-720 %"), ("toggles_nutrient_day", "nutrient toggles/d"), ("toggles_fan_day", "fan toggles/d"), ("toggles_tank_pump_day", "tank pump toggles/d"),
        ("level_min_pct", "Level min %"), ("soc_min_pct", "SoC min %"), ("blackout_h", "Blackout h"),
        ("energy_used_wh_day", "Used Wh/d"), ("energy_in_wh_day", "Solar Wh/d"),
        ("ph_toggles_day", "pH relay toggles/d"), ("ph_out_of_band_s", "pH out-of-band s"), ("ph_excursion_max", "pH max excursion"), ("pdr_pct", "PDR %"),
        ("latency_mean_ms", "Lat mean ms"), ("resp_mean_ms", "Resp mean ms")]
lines = ["| Scenario | " + " | ".join(c[1] for c in cols) + " |",
         "|---|" + "---|" * len(cols)]
for n, r in results.items():
    if n.startswith("_"):
        continue
    lines.append(f"| {n} | " + " | ".join(f"{r[c[0]]:.1f}" if r[c[0]] == r[c[0]] else "n/a" for c in cols) + " |")
lines += ["", f"Simulated frame length: {frame_len} bytes", "",
          "| Baud | Serialization ms (one frame) |", "|---|---|"]
lines += [f"| {b} | {v:.1f} |" for b, v in baud_tbl.items()]
open(os.path.join(OUT, "summary.md"), "w").write("\n".join(lines) + "\n")

# ---- plots ---------------------------------------------------------------
def plot(name, fname):
    r = series[name]
    th = [x["t_h"] for x in r]
    fig, ax = plt.subplots(5, 1, figsize=(10, 11), sharex=True)
    ax[0].plot(th, [x["air_c"] for x in r], label="air"); ax[0].plot(th, [x["water_c"] for x in r], label="water")
    ax[0].axhline(30, ls=":", c="r"); ax[0].set_ylabel("Temp C"); ax[0].legend(loc="upper right")
    ax[1].plot(th, [x["ph"] for x in r]); ax[1].axhspan(6.5, 7.2, alpha=.15, color="g"); ax[1].set_ylabel("pH")
    ax[2].plot(th, [x["tds"] for x in r]); ax[2].axhspan(600, 620, alpha=.4, color="g"); ax[2].set_ylabel("TDS ppm")
    ax[3].plot(th, [x["level"] for x in r]); ax[3].axhline(40, ls=":", c="r"); ax[3].axhline(70, ls=":", c="g"); ax[3].set_ylabel("Level %")
    ax[4].plot(th, [x["soc_pct"] for x in r]); ax[4].set_ylabel("Battery %"); ax[4].set_xlabel("Hours")
    fig.suptitle(f"SAOS simulation - {name}")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, fname), dpi=130); plt.close(fig)

plot("S1_baseline", "S1_baseline.png")
plot("S2_heatwave_+6C", "S2_heatwave.png")
plot("S3_cloudy_30pct", "S3_cloudy.png")

# pH strategy comparison
fig, ax = plt.subplots(figsize=(10, 4))
for n, lab in (("S1_baseline", "continuous (firmware)"), ("S4_pH_pulse_dosing", "pulse + wait (proposed)")):
    ax.plot([x["t_h"] for x in series[n]], [x["ph"] for x in series[n]], label=lab)
ax.axhspan(6.5, 7.2, alpha=.15, color="g"); ax.set_xlabel("Hours"); ax.set_ylabel("pH"); ax.legend()
ax.set_title("pH dosing strategy (calm day)"); ax.set_xlim(0, 36)
fig2, ax2 = plt.subplots(figsize=(10, 4))
for n, lab in (("S7_pH_shock_continuous", "continuous (firmware)"), ("S8_pH_shock_pulse", "pulse + wait (proposed)")):
    ax2.plot([x["t_h"] for x in series[n]], [x["ph"] for x in series[n]], label=lab)
ax2.axhspan(6.5, 7.2, alpha=.15, color="g"); ax2.set_xlim(8, 20); ax2.set_xlabel("Hours"); ax2.set_ylabel("pH")
ax2.set_title("Recovery from a -0.9 pH shock at t=10 h"); ax2.legend()
fig2.tight_layout(); fig2.savefig(os.path.join(OUT, "ph_shock.png"), dpi=130)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "ph_strategy.png"), dpi=130)
print(open(os.path.join(OUT, "summary.md")).read())
