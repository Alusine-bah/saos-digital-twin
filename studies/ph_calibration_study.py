"""Monte Carlo comparison of pH calibration methods, using the project's own buffer data as the probe truth.

ASSUMPTIONS (to be replaced by literature/bench values):
  * probe response is linear, V = v7 + s*(pH-7)*T_K/298.15 (Nernst slope scaling)
  * voltage noise after averaging: 2 mV (1 sigma)
  * buffer pH uncertainty: 0.02 pH (1 sigma)
  * truth slope/offset come from the recorded two-point buffer test (pH 4.01 at 2.925 V, pH 6.86 at 2.314 V, taken at 25 C)
"""
import os, sys, math, random, subprocess, tempfile
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, ".."))
OUT = os.path.join(HERE, "..", "results"); os.makedirs(OUT, exist_ok=True)

S_TRUE = (2.314 - 2.925) / (6.86 - 4.01)             # V per pH
V7_TRUE = 2.925 + S_TRUE * (7 - 4.01)
SIG_V, SIG_BUF = 0.002, 0.02


def probe_v(ph, T):
    return V7_TRUE + S_TRUE * (ph - 7.0) * (T + 273.15) / 298.15


def fit(points):
    x = np.array([p - 7 for _, p, _ in points]); y = np.array([v for v, _, _ in points])
    s, a = np.polyfit(x, y, 1)
    return s, a, float(np.mean([t for _, _, t in points]))


def read_method(method, v, T, cal):
    if method == "v1":
        return -5.70 * v + 21.34
    s, a, tref = cal
    scale = (T + 273.15) / (tref + 273.15) if method.endswith("temp") else 1.0
    return 7.0 + (v - a) / (s * scale)


def run(n=4000, seed=3):
    rng = random.Random(seed)
    grid = [5.0, 5.5, 6.0, 6.5, 6.86, 7.0, 7.2, 7.5, 8.0, 8.5, 9.0]
    temps = [20, 25, 30, 35]
    methods = {"v1": "v1 tutorial constants (no calibration)", "2pt": "2-point (4.01/6.86), no temp comp",
               "2pt_temp": "2-point + temperature comp", "3pt_temp": "3-point (4.01/6.86/9.18) + temp comp"}
    err = {m: {(T, p): [] for T in temps for p in grid} for m in methods}
    for _ in range(n):
        cal2 = fit([(probe_v(b, 25) + rng.gauss(0, SIG_V), b + rng.gauss(0, SIG_BUF), 25) for b in (4.01, 6.86)])
        cal3 = fit([(probe_v(b, 25) + rng.gauss(0, SIG_V), b + rng.gauss(0, SIG_BUF), 25) for b in (4.01, 6.86, 9.18)])
        for T in temps:
            for p in grid:
                v = probe_v(p, T) + rng.gauss(0, SIG_V)
                err["v1"][(T, p)].append(read_method("v1", v, T, None) - p)
                err["2pt"][(T, p)].append(read_method("2pt", v, T, cal2) - p)
                err["2pt_temp"][(T, p)].append(read_method("2pt_temp", v, T, cal2) - p)
                err["3pt_temp"][(T, p)].append(read_method("3pt_temp", v, T, cal3) - p)
    return methods, err, grid, temps


def rms(a): return math.sqrt(sum(x * x for x in a) / len(a))


def cpp_parity():
    """C++ calibfit must agree with numpy polyfit on random calibrations."""
    exe = os.path.join(HERE, "..", "core", "build", "calibfit")
    subprocess.run(["make", "-s", "-C", os.path.join(HERE, "..", "core"), "all"], check=True)
    rng = random.Random(9); worst = 0.0
    for _ in range(50):
        pts = [(probe_v(b, 25) + rng.gauss(0, 0.004), b, 25.0) for b in (4.01, 6.86, 9.18)]
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
            f.write("v,ph,t\n"); [f.write(f"{v!r},{p!r},{t!r}\n") for v, p, t in pts]
        out = subprocess.run([exe, f.name], capture_output=True, text=True, check=True).stdout
        kv = dict(l.split("=") for l in out.splitlines()); os.unlink(f.name)
        s, a, _ = fit(pts)
        worst = max(worst, abs(float(kv["slope"]) - s), abs(float(kv["v7"]) - a))
    return worst


if __name__ == "__main__":
    methods, err, grid, temps = run()
    band = [p for p in grid if 6.5 <= p <= 7.2]
    rows = ["# pH calibration study (Monte Carlo, 4000 calibrations)", "",
            "Probe truth = the project's own two-point buffer data. Voltage noise 2 mV, buffer tolerance 0.02 pH (assumed).", "",
            "| Method | RMS error over pH 5-9, all temps | RMS error in control band 6.5-7.2, 25 C | Worst mean error, any pH/temp |", "|---|---|---|---|"]
    for m, name in methods.items():
        allv = [x for k, v in err[m].items() for x in v]
        bandv = [x for p in band for x in err[m][(25, p)]]
        worst = max(abs(sum(v) / len(v)) for v in err[m].values())
        rows.append(f"| {name} | {rms(allv):.3f} | {rms(bandv):.3f} | {worst:.2f} |")
    worst_c = cpp_parity()
    rows += ["", f"C++ `saos_calib` vs numpy `polyfit` on 50 random calibrations: max difference {worst_c:.2e} (slope and v7).", ""]
    open(os.path.join(OUT, "ph_calibration_study.md"), "w").write("\n".join(rows) + "\n")
    fig, ax = plt.subplots(1, 2, figsize=(12, 4), sharey=True)
    for a, T in zip(ax, (25, 35)):
        for m, name in methods.items():
            a.plot(grid, [sum(err[m][(T, p)]) / len(err[m][(T, p)]) for p in grid], "o-", label=name)
        a.axhline(0, c="k", lw=.5); a.axvspan(6.5, 7.2, alpha=.1, color="g"); a.set_title(f"Mean reading error at {T} C"); a.set_xlabel("true pH"); a.grid(alpha=.3)
    ax[0].set_ylabel("reading - true (pH)"); ax[0].legend(fontsize=7)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "ph_calibration_study.png"), dpi=130)
    print("\n".join(rows))
