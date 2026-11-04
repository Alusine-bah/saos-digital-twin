import os, sys, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "studies"))
import ph_calibration_study as st
from saos_sim.config import Params
from saos_sim.sim import run, with_


def test_cpp_calibration_matches_numpy():
    assert st.cpp_parity() < 1e-9


def test_calibrated_beats_tutorial_constants():
    methods, err, grid, temps = st.run(n=300)
    r = lambda m: st.rms([x for v in err[m].values() for x in v])
    assert r("v1") > 1.0 and r("2pt_temp") < 0.06 and r("3pt_temp") <= r("2pt_temp")


def test_closed_loop_with_bad_vs_good_calibration():
    bad, _ = run(with_(Params(days=2.0), ph_cal_gain=1.222, ph_cal_offset=-0.233))
    good, _ = run(with_(Params(days=2.0)))
    assert bad["ph_true_min"] < 6.0 and good["ph_true_min"] > 6.4


def test_alkalinity_model_matches_carbonate_relation_and_literature():
    from saos_sim.config import alk_loss_from_feed
    from saos_sim.plant import Plant
    import math
    p = with_(Params(), alk_ref_mgl=100.0, ph_ref=7.1)
    pl = Plant(p)
    assert abs(pl.ph - 7.1) < 1e-9
    pl.alk *= 10 ** 0.3
    pl.ph = p.ph_ref + math.log10(pl.alk / p.alk_ref_mgl)
    assert abs(pl.ph - 7.4) < 1e-9
    # UVI-derived net loss and the stoichiometric formula
    kg = 40.65 * 1.351 + 38.85 * 0.892
    assert abs(kg * 1e6 / 111196 / 365 - 2.21) < 0.02
    assert abs(alk_loss_from_feed(1000, 1000) - 214.2) < 0.5       # 1 kg feed in 1 m3 per day
    low, _ = run(with_(Params(days=6.0), alk_ref_mgl=50.0, alk_loss_mgl_day=41.0))
    none, _ = run(with_(Params(days=6.0), alk_ref_mgl=200.0, alk_loss_mgl_day=2.2))
    assert low["ph_pump_on_s_day"] > 0 and none["ph_pump_on_s_day"] == 0


def test_prototype_estimate_numbers():
    from saos_sim.config import alk_loss_from_feed, PROTOTYPE_ESTIMATE
    assert abs(alk_loss_from_feed(8, 35) - 49.0) < 0.5
    off = PROTOTYPE_ESTIMATE["plant_offset"]
    assert abs(alk_loss_from_feed(8, 35, plant_offset=off) - 2.9) < 0.1
    assert abs(alk_loss_from_feed(99.6 * 214, 111196) - 41.1) < 0.2


def test_fan_ventilation_heat_balance_numbers():
    from saos_sim.config import fan_vent_fraction_from_ach
    assert abs(fan_vent_fraction_from_ach(1.0) - 0.57) < 0.01
    assert abs(fan_vent_fraction_from_ach(1.5) - 0.67) < 0.01
    assert abs(fan_vent_fraction_from_ach(1.0, u_w_m2k=5.0) - 0.70) < 0.01
    # with the fan on the simulated air must be cooler than the same run with the fan forced off
    on, _ = run(with_(Params(days=2.0)))
    off, _ = run(with_(Params(days=2.0), fan_on_c=99.0, fan_off_c=98.0))
    assert on["air_max_c"] < off["air_max_c"] - 2.0
