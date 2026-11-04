"""Closed-loop simulation runner and benchmark metrics."""
import csv
import dataclasses
from .config import Params
from .plant import Plant, Sensors
from .controller import MegaController
from .link import Link, build_frame


def run(p: Params, esp_overrides=None, log_every: int = 60, csv_path=None, trace=None):
    """esp_overrides: list of (t_start_s, t_end_s, device, on) forced from the ESP32."""
    plant = Plant(p)
    sens = Sensors(plant, seed=p.seed + 6)   # seed 1 -> 7, as before
    ctl, link = MegaController(p), Link(p)
    esp_overrides = esp_overrides or []
    steps = int(p.days * 86400 / p.dt)
    rows = []
    m = dict(water_ok=0, ph_on_s=0, first_dose_s=-1.0, ph_min=14.0, ph_over_max=0.0, ph_rec_s=0, n=0, ph_in=0, air_ok=0, tds_in=0, level_ok=0, ph_dev_max=0.0,
             air_max=0.0, level_min=100.0, soc_min=100.0, blackout_s=0)
    next_frame = 0.0
    last_hb = {}
    for i in range(steps):
        t = plant.t
        # ESP32 commands (re-sent each second while active, like the dashboard heartbeat)
        for (t0, t1, dev, on) in esp_overrides:
            if t0 <= t < t1 and int(t) % 2 == 0:
                if dev not in last_hb or last_hb[dev] != int(t):
                    link.command_response_ms()
                    last_hb[dev] = int(t)
                ctl.esp_command(t, dev, on)
        s = sens.read()
        act = ctl.tick(t, s, plant.hour()) if int(t) % 1 == 0 else ctl.st
        if trace is not None:
            trace.append((t, plant.hour(), s, dict(act)))
        plant.step(act)
        if t >= next_frame:
            link.send_telemetry(build_frame(s, act, t))
            next_frame = t + p.frame_period_s
        # metrics
        m["n"] += 1
        m["ph_in"] += p.ph_low - 0.05 <= plant.ph <= p.ph_high + 0.05
        m["air_ok"] += plant.air_c <= 35.0
        m["water_ok"] += 25.0 <= plant.water_c <= 30.0
        m["tds_in"] += p.tds_low <= plant.tds <= p.tds_high + 100
        m["level_ok"] += plant.level >= p.level_low - 5
        m["ph_over_max"] = max(m["ph_over_max"], plant.ph - p.ph_high, p.ph_low - plant.ph)
        if p.ph_shock_h >= 0 and t > p.ph_shock_h * 3600 and not (p.ph_low <= plant.ph <= p.ph_high):
            m["ph_rec_s"] += 1
        m["ph_min"] = min(m["ph_min"], plant.ph)
        if act["ph_up"] or act["ph_down"]:
            m["ph_on_s"] += 1
            if m["first_dose_s"] < 0:
                m["first_dose_s"] = t
        m["ph_dev_max"] = max(m["ph_dev_max"], abs(plant.ph - 7.1))
        m["air_max"] = max(m["air_max"], plant.air_c)
        m["level_min"] = min(m["level_min"], plant.level)
        soc = 100 * plant.soc_wh / p.battery_wh_usable
        m["soc_min"] = min(m["soc_min"], soc)
        m["blackout_s"] += plant.soc_wh <= 0.0
        if i % int(log_every / p.dt) == 0:
            rows.append(dict(t_h=t / 3600, air_c=plant.air_c, water_c=plant.water_c, ph=plant.ph,
                             tds=plant.tds, level=plant.level, soc_pct=soc, load_w=plant.load_w,
                             gen_w=plant.gen_w, sun=plant.sun, **{k: int(v) for k, v in act.items()}))
    n = m["n"]
    days = p.days
    res = dict(
        ph_in_band_pct=100 * m["ph_in"] / n,
        air_below_35c_pct=100 * m["air_ok"] / n,
        water_25_30_pct=100 * m["water_ok"] / n,
        tds_in_band_pct=100 * m["tds_in"] / n,
        level_ok_pct=100 * m["level_ok"] / n,
        ph_true_min=m["ph_min"], ph_pump_on_s_day=m["ph_on_s"] / days, first_dose_day=(m["first_dose_s"] / 86400.0 if m["first_dose_s"] >= 0 else None), ph_max_dev=m["ph_dev_max"], ph_excursion_max=m["ph_over_max"], ph_out_of_band_s=m["ph_rec_s"], air_max_c=m["air_max"], level_min_pct=m["level_min"],
        soc_min_pct=m["soc_min"], blackout_h=m["blackout_s"] / 3600.0,
        energy_used_wh_day=plant.energy_used_wh / days,
        energy_in_wh_day=plant.energy_in_wh / days,
        **{f"toggles_{k}_day": v / days for k, v in ctl.toggles.items()},
        ph_toggles_day=(ctl.toggles["ph_up"] + ctl.toggles["ph_down"]) / days,
        **link.summary(),
    )
    if csv_path and rows:
        with open(csv_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
    return res, rows


def with_(p: Params, **kw) -> Params:
    return dataclasses.replace(p, **kw)
