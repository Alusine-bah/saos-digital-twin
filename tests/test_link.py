import os, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pytest

CORE = os.path.join(os.path.dirname(__file__), "..", "core")
BIN = os.path.join(CORE, "build", "linkbench")


@pytest.fixture(scope="session", autouse=True)
def build():
    subprocess.run(["make", "-s", "-C", CORE, "all"], check=True)


def bench(**kw):
    out = subprocess.run([BIN] + [f"{k}={v}" for k, v in kw.items()], check=True, capture_output=True, text=True).stdout
    d = {}
    for line in out.splitlines():
        k, v = line.split("=")
        try:
            d[k] = float(v)
        except ValueError:
            d[k] = v
    return d


def test_deterministic_for_same_seed():
    assert bench(mode="v2", ber=1e-4, seconds=600, seed=5) == bench(mode="v2", ber=1e-4, seconds=600, seed=5)


def test_v2_never_accepts_damaged_frames():
    for ber in (1e-4, 1e-3, 3e-3):
        r = bench(mode="v2", baud=115200, ber=ber, seconds=3600)
        assert r["silent_wrong_or_undetected"] == 0


def test_v1_cannot_detect_damage():
    r = bench(mode="v1", baud=9600, ber=1e-4, seconds=3600)
    assert r["silent_wrong_or_undetected"] > 100


def test_clean_channel_v2_fast_and_complete():
    r = bench(mode="v2", baud=115200, seconds=1800)
    assert r["pdr_pct"] == 100.0 and r["latency_max_ms"] < 10 and r["cmd_success_pct"] == 100.0
    assert r["wire_bytes_per_frame"] == 32.0


def test_v1_stalls_mega_and_is_much_slower():
    v1 = bench(mode="v1", baud=9600, seconds=1800)
    v2 = bench(mode="v2", baud=115200, seconds=1800)
    assert v1["mega_tx_stall_ms_per_s"] > 100 and v2["mega_tx_stall_ms_per_s"] == 0
    assert v1["latency_mean_ms"] > 20 * v2["latency_mean_ms"]


def test_retries_recover_commands_on_noisy_link():
    r = bench(mode="v2", baud=115200, ber=3e-3, seconds=3600)
    assert r["cmd_success_pct"] > 90 and r["avg_tries_per_cmd"] > 1.0
