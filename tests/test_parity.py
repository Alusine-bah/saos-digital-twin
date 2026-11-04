"""Parity: the C++ control core must reproduce the Python twin's decisions second by second."""
import os, subprocess, sys, csv, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pytest
from saos_sim.config import Params
from saos_sim.sim import run, with_

CORE = os.path.join(os.path.dirname(__file__), "..", "core")
REPLAY = os.path.join(CORE, "build", "replay")
KEYS = ["fan", "ph_up", "ph_down", "nutrient", "light", "tank_pump"]


@pytest.fixture(scope="session", autouse=True)
def build():
    subprocess.run(["make", "-s", "-C", CORE, "all"], check=True)


def parity(p, args, tmp_path):
    trace = []
    run(p, trace=trace, log_every=3600)
    tf = tmp_path / "trace.csv"
    with open(tf, "w") as f:
        f.write("t_s,hour,air_c,ph,tds,level,level_new,lux\n")
        for t, hour, s, _ in trace:
            f.write(f"{t!r},{hour!r},{s['air_c']!r},{s['ph']!r},{s['tds']!r},{s['level']!r},"
                    f"{int(s['level_new'])},{s['lux']!r}\n")
    out = subprocess.run([REPLAY, str(tf)] + args, check=True, capture_output=True, text=True).stdout
    rows = list(csv.DictReader(out.splitlines()))
    assert len(rows) == len(trace)
    bad = 0
    for (t, _, _, act), r in zip(trace, rows):
        for k in KEYS:
            if int(act[k]) != int(r[k]):
                bad += 1
    return bad, len(trace)


def test_parity_v1_baseline(tmp_path):
    bad, n = parity(with_(Params(), days=2.0), [], tmp_path)   # 2 days: tank pump fires
    assert bad == 0, f"{bad} mismatching outputs over {n} steps"


def test_parity_pulse_dosing_with_shock(tmp_path):
    p = with_(Params(), days=1.0, ph_strategy="pulse", ph_shock_h=4.0, ph_shock_delta=-0.9)
    bad, n = parity(p, ["pulse=1"], tmp_path)
    assert bad == 0, f"{bad} mismatches / {n}"


def test_parity_continuous_with_shock(tmp_path):
    p = with_(Params(), days=1.0, ph_shock_h=4.0, ph_shock_delta=-0.9)
    bad, n = parity(p, [], tmp_path)
    assert bad == 0, f"{bad} mismatches / {n}"


def test_parity_with_automatic_light(tmp_path):
    p = with_(Params(), days=1.0, light_auto=True, cloud_factor=0.2)
    bad, n = parity(p, ["light_auto=1"], tmp_path)
    assert bad == 0, f"{bad} mismatches / {n}"


def test_parity_heatwave(tmp_path):
    bad, n = parity(with_(Params(), days=1.0, heatwave_c=6.0), [], tmp_path)
    assert bad == 0


def test_parity_ph_down_continuous(tmp_path):
    p = with_(Params(), days=1.0, ph_shock_h=4.0, ph_shock_delta=+1.2)
    bad, n = parity(p, [], tmp_path)
    assert bad == 0


def test_parity_ph_down_pulse(tmp_path):
    p = with_(Params(), days=1.0, ph_strategy="pulse", ph_shock_h=4.0, ph_shock_delta=+1.2)
    bad, n = parity(p, ["pulse=1"], tmp_path)
    assert bad == 0


def test_parity_exercises_every_actuator():
    """Guard against vacuous parity: the traces together must switch every device."""
    seen = set()
    for kw in (dict(days=2.0, level_loss_per_h=0.9), dict(days=1.0, ph_shock_h=4.0, ph_shock_delta=+1.2),
               dict(days=1.0, ph_shock_h=4.0, ph_shock_delta=-0.9),
               dict(days=1.0, light_auto=True, cloud_factor=0.2)):
        tr = []
        run(with_(Params(), **kw), trace=tr, log_every=3600)
        prev = None
        for _, _, _, a in tr:
            if prev:
                seen |= {k for k in a if a[k] != prev[k]}
            prev = a
    assert seen == set(KEYS), f"never switched: {set(KEYS) - seen}"


def test_parity_with_dwell_timers(tmp_path):
    bad, n = parity(with_(Params(), days=2.0, min_on_s=300.0, min_off_s=300.0), ["min_on_s=300", "min_off_s=300"], tmp_path)
    assert bad == 0, f"{bad} mismatching outputs over {n} steps"
    # and the dwell actually reduced fan switching versus v1
    v1, _ = run(with_(Params(), days=2.0))
    v2, _ = run(with_(Params(), days=2.0, min_on_s=300.0, min_off_s=300.0))
    assert v2["toggles_fan_day"] < 0.5 * v1["toggles_fan_day"]
