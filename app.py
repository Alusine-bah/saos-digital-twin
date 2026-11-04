"""SAOS digital twin: interactive demo.  Run:  streamlit run app.py
Change the parameters on the left, press nothing: the simulation reruns and shows the result.
Everything shown is SIMULATED. Plant values are literature-based estimates (docs/LITERATURE.md), not measurements of the prototype."""
import dataclasses
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from saos_sim.config import Params, fan_vent_fraction_from_ach
from saos_sim.sim import run, with_

st.set_page_config(page_title="SAOS digital twin", layout="wide")

PRESETS = {
    "v1 as built (outdoor, 29 C mean)": {},
    "Indoor mode": dict(solar_gain_c=1.5, amb_swing_c=2.0, amb_mean_c=28.0),
    "Heatwave +6 C": dict(heatwave_c=6.0),
    "Cloudy week (30 % sun)": dict(cloud_factor=0.3),
    "pH shock at 10 h (-0.9)": dict(ph_shock_h=10.0, ph_shock_delta=-0.9),
    "Recommended redesign": dict(min_on_s=300.0, min_off_s=300.0, solar_gain_c=6.0, panel_w=150.0, battery_wh_usable=240.0, tds_high=700.0),
}

st.title("SAOS digital twin: aquaponics controller simulator")
st.caption("Arduino Mega + ESP32 aquaponics system, rebuilt as software. All results are simulated; plant parameters are estimates "
           "tagged in docs/LITERATURE.md. Replace them with measurements to turn this into a prediction of a real prototype.")

preset = st.sidebar.selectbox("Scenario preset", list(PRESETS), index=0)
base = dataclasses.replace(Params(days=3.0), **PRESETS[preset])


def num(label, field, lo, hi, step, help=None):
    return st.slider(label, float(lo), float(hi), float(getattr(base, field)), float(step), help=help, key=f"{preset}-{field}")


with st.sidebar.expander("Run", expanded=True):
    days = st.slider("Days simulated", 1, 14, 3, key="days")
    seed = st.number_input("Noise seed", 1, 999, 1, key="seed")
with st.sidebar.expander("Weather and site"):
    amb_mean = num("Mean ambient (C)", "amb_mean_c", 10, 40, 0.5)
    amb_swing = num("Daily swing +/- (C)", "amb_swing_c", 0, 10, 0.5)
    heat = num("Heatwave offset (C)", "heatwave_c", 0, 10, 0.5)
    cloud = num("Sun factor (1 = clear)", "cloud_factor", 0.1, 1.0, 0.05)
with st.sidebar.expander("Fan and climate"):
    gain = num("Solar rise without fan (K)", "solar_gain_c", 0, 20, 0.5, "12 K for a 3 m greenhouse, 6 K with shade net, 1.5 K indoors")
    ach = st.slider("Fan capacity (air changes per minute)", 0.2, 3.0, 1.0, 0.1, key="ach",
                    help="1.0-1.5 recommended for summer (SRAC 5008, UF/IFAS AE-10)")
    vent = fan_vent_fraction_from_ach(ach)
    st.caption(f"Share of solar rise removed by the fan: {vent:.2f}")
    fan_on = num("Fan on at (C)", "fan_on_c", 20, 40, 0.5)
    fan_off = num("Fan off at (C)", "fan_off_c", 15, 38, 0.5)
    dht = num("DHT11 bias (C)", "dht_bias_c", -3, 3, 0.5, "DHT11 accuracy is +/-2 C")
    dwell = num("Minimum on/off time, fan/tank pump/light (s)", "min_on_s", 0, 900, 30, "Not applied to dosing pumps")
with st.sidebar.expander("pH"):
    ph_low = num("pH low limit", "ph_low", 5.5, 7.5, 0.1)
    ph_high = num("pH high limit", "ph_high", 6.5, 8.0, 0.1)
    alk_loss = num("Net alkalinity loss (mg/L/day)", "alk_loss_mgl_day", 0.5, 30, 0.5, "Estimated 1-8 for the prototype; UVI net 2.2")
    strategy = st.selectbox("Dosing strategy", ["continuous", "pulse"], index=0 if base.ph_strategy == "continuous" else 1)
    ph_off = num("pH probe error (offset)", "ph_cal_offset", -1.0, 1.0, 0.05)
with st.sidebar.expander("TDS and water"):
    tds_low = num("TDS low (ppm)", "tds_low", 300, 900, 10)
    tds_high = num("TDS high (ppm)", "tds_high", 320, 1000, 10, "v1 used a 20 ppm band; the sensor is only +/-100 ppm accurate")
    tds_bias = num("TDS sensor bias (ppm)", "tds_bias_ppm", -150, 150, 10)
    loss = num("Water loss (% of level scale per hour)", "level_loss_per_h", 0.05, 1.0, 0.01, "0.17 derived; v1 guessed 0.9")
with st.sidebar.expander("Power"):
    panel = num("Solar panel (W)", "panel_w", 20, 300, 10)
    batt = num("Usable battery (Wh)", "battery_wh_usable", 40, 500, 10, "12 V 20 Ah at 50 % DoD = 120 Wh")
    base_w = num("Electronics base load (W)", "p_base_w", 1.0, 8.0, 0.2, "4.2 kept; component sum about 2.2")


@st.cache_data(show_spinner="Simulating...")
def simulate(params: dict):
    p = Params(**params)
    res, rows = run(p, log_every=60)
    return res, pd.DataFrame(rows)


params = dataclasses.asdict(dataclasses.replace(
    base, days=float(days), seed=int(seed), amb_mean_c=amb_mean, amb_swing_c=amb_swing, heatwave_c=heat, cloud_factor=cloud,
    solar_gain_c=gain, fan_vent_fraction=round(vent, 3), fan_on_c=fan_on, fan_off_c=fan_off, dht_bias_c=dht,
    min_on_s=dwell, min_off_s=dwell, ph_low=ph_low, ph_high=ph_high, alk_loss_mgl_day=alk_loss, ph_strategy=strategy,
    ph_cal_offset=ph_off, tds_low=tds_low, tds_high=tds_high, tds_bias_ppm=tds_bias, level_loss_per_h=loss,
    panel_w=panel, battery_wh_usable=batt, p_base_w=base_w))
res, df = simulate(params)

max_tog = max(v for k, v in res.items() if k.startswith("toggles_") and k.endswith("_day"))
checks = [
    ("pH in band at least 95 % of the time", res["ph_in_band_pct"], ">=", 95.0),
    ("Air under 35 C at least 90 % of the time", res["air_below_35c_pct"], ">=", 90.0),
    ("Water 25-30 C (tilapia) at least 80 % of the time", res["water_25_30_pct"], ">=", 80.0),
    ("TDS in 600-720 ppm at least 90 % of the time", res["tds_in_band_pct"], ">=", 90.0),
    ("No battery blackout", res["blackout_h"], "<=", 0.0),
    ("Each relay switches at most 100 times per day", max_tog, "<=", 100.0),
    ("Tank level never below 35 %", res["level_min_pct"], ">=", 35.0),
]
c = st.columns(6)
c[0].metric("pH in band", f"{res['ph_in_band_pct']:.0f} %")
c[1].metric("Air max", f"{res['air_max_c']:.1f} C")
c[2].metric("Water in 25-30 C", f"{res['water_25_30_pct']:.0f} %")
c[3].metric("Fan switches / day", f"{res['toggles_fan_day']:.0f}")
c[4].metric("Battery blackout", f"{res['blackout_h']:.1f} h")
c[5].metric("Energy per day", f"{res['energy_used_wh_day']:.0f} Wh")

tab1, tab2, tab3 = st.tabs(["Time series", "Requirement checks", "Parameters and download"])
with tab1:
    fig, ax = plt.subplots(6, 1, figsize=(11, 13), sharex=True)
    ax[0].plot(df.t_h, df.air_c, label="air"); ax[0].plot(df.t_h, df.water_c, label="water")
    ax[0].axhline(fan_on, ls=":", c="r"); ax[0].axhspan(25, 30, alpha=.08, color="g"); ax[0].set_ylabel("Temp C"); ax[0].legend(loc="upper right")
    ax[1].plot(df.t_h, df.ph); ax[1].axhspan(ph_low, ph_high, alpha=.15, color="g"); ax[1].set_ylabel("pH")
    ax[2].plot(df.t_h, df.tds); ax[2].axhspan(tds_low, tds_high, alpha=.2, color="g"); ax[2].set_ylabel("TDS ppm")
    ax[3].plot(df.t_h, df.level); ax[3].axhline(40, ls=":", c="r"); ax[3].axhline(70, ls=":", c="g"); ax[3].set_ylabel("Level %")
    ax[4].plot(df.t_h, df.soc_pct, label="battery %"); ax[4].plot(df.t_h, df.gen_w, label="solar W", alpha=.6); ax[4].set_ylabel("Power"); ax[4].legend(loc="upper right")
    for i, k in enumerate(["fan", "ph_up", "ph_down", "nutrient", "tank_pump", "light"]):
        ax[5].step(df.t_h, df[k] * 0.8 + i, where="post")
    ax[5].set_yticks([i + 0.4 for i in range(6)]); ax[5].set_yticklabels(["fan", "pH up", "pH down", "nutrient", "tank pump", "light"]); ax[5].set_xlabel("Hours")
    fig.tight_layout(); st.pyplot(fig); plt.close(fig)
with tab2:
    rows = []
    for name, val, op, thr in checks:
        ok = val >= thr if op == ">=" else val <= thr
        rows.append({"Check": name, "Result": round(val, 1), "Target": f"{op} {thr:g}", "Verdict": "PASS" if ok else "FAIL"})
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    st.caption("Single-run checks from the validation suite (validation/run_validation.py runs 12 requirements over 10 seeds).")
with tab3:
    st.json({k: v for k, v in params.items() if k in ("amb_mean_c", "solar_gain_c", "fan_vent_fraction", "level_loss_per_h", "panel_w", "battery_wh_usable")} | {"preset": preset})
    buf = io.StringIO(); df.to_csv(buf, index=False)
    st.download_button("Download time series (CSV)", buf.getvalue(), file_name="saos_run.csv", mime="text/csv")
    st.dataframe(pd.DataFrame([res]).T.rename(columns={0: "value"}), use_container_width=True)
