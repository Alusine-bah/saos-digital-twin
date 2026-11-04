"""Power budget: sun level, panel and battery size, base load, relay coils. 7 days, constant sun factor (a stress test, not a forecast)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from saos_sim.config import Params
from saos_sim.sim import run, with_
base = Params(days=7.0)
lines = ["# Power study (7 days, constant sun factor)", "",
         "Model clear-day yield = peak_sun_hours 5.0 x charge_eff 0.85 = 4.25 kWh per kW per day. Cited seasonal PV output (NASA POWER via profileSOLAR): Freetown 4.58-6.16, Savar (Dhaka area) 4.01-5.98 kWh/kW/day, so the model sits at the low end of both.", "",
         "| Case | Sun factor | Used Wh/day | Solar Wh/day | Blackout h in 7 d | SoC min % |", "|---|---|---|---|---|---|"]
def row(lab, p, sun):
    r, _ = run(with_(p, cloud_factor=sun), log_every=3600)
    lines.append(f"| {lab} | {sun:.2f} | {r['energy_used_wh_day']:.0f} | {r['energy_in_wh_day']:.0f} | {r['blackout_h']:.1f} | {r['soc_min_pct']:.0f} |"); print(lines[-1], flush=True)
for sun in (1.0, 0.85, 0.6, 0.45, 0.3):
    row("v1: 100 W, 120 Wh usable", base, sun)
for sun in (0.6, 0.45, 0.3):
    row("base load 2.2 W (component sum)", with_(base, p_base_w=2.2), sun)
    row("200 W panel", with_(base, panel_w=200.0), sun)
    row("150 W + 240 Wh usable", with_(base, panel_w=150.0, battery_wh_usable=240.0), sun)
row("relay coils off (v1 model before this topic)", with_(base, p_relay_coil_w=0.0), 1.0)
row("DoD 80 % (192 Wh usable, shorter battery life)", with_(base, battery_wh_usable=192.0), 0.3)
open(os.path.join(os.path.dirname(__file__), "..", "results", "power_study.md"), "w").write("\n".join(lines) + "\n")
