"""How the pH controller's workload depends on the (literature-bounded) alkalinity budget of the tank."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from saos_sim.config import Params
from saos_sim.sim import run, with_

OUT = os.path.join(os.path.dirname(__file__), "..", "results"); os.makedirs(OUT, exist_ok=True)
LOSS = [1.0, 2.9, 7.7, 49.0]       # mg/L CaCO3 per day: prototype net low/central/high, and gross (plants not offsetting)
ALK = [50.0, 100.0, 200.0]          # mg/L CaCO3 (UVI observed range 65-207)
DAYS = 10.0


def study():
    out = []
    for alk in ALK:
        for loss in LOSS:
            res, rows = run(with_(Params(), days=DAYS, alk_ref_mgl=alk, alk_loss_mgl_day=loss), log_every=60)
            first = res["first_dose_day"]
            out.append(dict(alk=alk, loss=loss, first_dose_day=first, ph_min=res["ph_true_min"],
                            in_band=res["ph_in_band_pct"], toggles_day=res["ph_toggles_day"],
                            pump_s_day=res["ph_pump_on_s_day"]))
    return out


if __name__ == "__main__":
    data = study()
    L = ["# pH controller workload vs alkalinity budget (10-day simulation)", "",
         "Loss values are the ESTIMATED prototype (feed 4-12 g/day, 20-50 L system, plants offsetting 94 % as in the UVI system): net 1.0 / 2.9 / 7.7 mg/L/day, and 49 mg/L/day gross (plants not offsetting).",
         "Alkalinity 50-200 mg/L as CaCO3 (UVI system 65-207); your tank's alkalinity is unknown and must be measured. Dosing strength is an ASSUMED parameter.", "",
         "| Alkalinity mg/L | Net loss mg/L/day | First dose (day) | True pH min | True pH in 6.5-7.2 % | Pump on-time s/day | Relay toggles/day |", "|---|---|---|---|---|---|---|"]
    for d in data:
        fd = f"{d['first_dose_day']:.1f}" if d["first_dose_day"] is not None else "none in 10 d"
        L.append(f"| {d['alk']:.0f} | {d['loss']} | {fd} | {d['ph_min']:.2f} | {d['in_band']:.1f} | {d['pump_s_day']:.0f} | {d['toggles_day']:.1f} |")
    open(os.path.join(OUT, "ph_drift_sensitivity.md"), "w").write("\n".join(L) + "\n")
    fig, ax = plt.subplots(figsize=(8, 4))
    for alk in ALK:
        sel = [d for d in data if d["alk"] == alk]
        ax.plot([d["loss"] for d in sel], [d["pump_s_day"] for d in sel], "o-", label=f"alkalinity {alk:.0f} mg/L")
    ax.set_xscale("log"); ax.set_xlabel("Net alkalinity loss (mg/L CaCO3 per day)"); ax.set_ylabel("pH pump on-time (s per day)")
    ax.set_title("pH dosing workload vs tank alkalinity budget"); ax.legend(); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "ph_drift_sensitivity.png"), dpi=130)
    print("\n".join(L))
