"""Fan behaviour vs enclosure thermal parameters and DHT11 error (literature-bounded)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from saos_sim.config import Params, fan_vent_fraction_from_ach
from saos_sim.sim import run, with_

OUT = os.path.join(os.path.dirname(__file__), "..", "results"); os.makedirs(OUT, exist_ok=True)
TAU = [300.0, 900.0, 2400.0]                         # small enclosure .. greenhouse (40 min)
VENT = [round(fan_vent_fraction_from_ach(1.0), 2), 0.60, round(fan_vent_fraction_from_ach(1.5, 5.0), 2)]


def study():
    rows = []
    for heat in (0.0, 6.0):
        for tau in TAU:
            for v in VENT:
                r, _ = run(with_(Params(), days=3.0, tau_air_s=tau, fan_vent_fraction=v, heatwave_c=heat), log_every=600)
                rows.append(dict(heat=heat, tau=tau, vent=v, toggles=r["toggles_fan_day"], air_max=r["air_max_c"],
                                 hot=100 - r["air_below_35c_pct"], water_ok=r["water_25_30_pct"]))
    for bias in (-2.0, 0.0, 2.0):
        r, _ = run(with_(Params(), days=3.0, dht_bias_c=bias), log_every=600)
        rows.append(dict(heat=0.0, tau=900.0, vent=0.60, bias=bias, toggles=r["toggles_fan_day"], air_max=r["air_max_c"],
                         hot=100 - r["air_below_35c_pct"], water_ok=r["water_25_30_pct"]))
    return rows


if __name__ == "__main__":
    rows = study()
    L = ["# Climate sensitivity (3-day simulation, fan 30 C on / 28 C off as in the firmware)", "",
         "Time constant range: small enclosure (300 s) to greenhouse (2400 s, about 40 min, Albright et al. 1985). Fan removal fraction 0.57-0.78 from a heat balance at 1.0-1.5 air changes per minute.", "",
         "| Heat wave | Air time constant s | Fan removes | DHT11 bias | Fan toggles/day | Air max C | Time above 35 C % | Water within 25-30 C % |", "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| +{r['heat']:.0f} C | {r['tau']:.0f} | {r['vent']:.2f} | {r.get('bias', 0):+.0f} | {r['toggles']:.0f} | {r['air_max']:.1f} | {r['hot']:.1f} | {r['water_ok']:.0f} |")
    open(os.path.join(OUT, "climate_sensitivity.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))
