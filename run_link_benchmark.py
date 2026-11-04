"""Stage 2 benchmark: v1 ASCII link vs v2 binary link across channel quality."""
import os, subprocess
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CORE = os.path.join(os.path.dirname(__file__), "core")
BIN = os.path.join(CORE, "build", "linkbench")
OUT = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(OUT, exist_ok=True)
subprocess.run(["make", "-s", "-C", CORE, "all"], check=True)


def bench(mode, baud, ber, seconds=7200, seeds=(1, 2, 3), **kw):
    acc = {}
    for sd in seeds:
        args = [BIN, f"mode={mode}", f"baud={baud}", f"ber={ber}", f"seconds={seconds}", f"seed={sd}"] + [f"{k}={v}" for k, v in kw.items()]
        out = subprocess.run(args, check=True, capture_output=True, text=True).stdout
        for line in out.splitlines():
            k, v = line.split("=")
            try:
                x = float(v)
            except ValueError:
                continue
            acc.setdefault(k, []).append(x)
    return {k: sum(v) / len(v) for k, v in acc.items()}


CONFIGS = [("v1 ASCII @9600 (as built)", "v1", 9600), ("v2 binary @9600", "v2", 9600), ("v2 binary @115200", "v2", 115200)]
BERS = [0.0, 1e-5, 1e-4, 1e-3, 3e-3]
res = {name: [bench(m, b, ber) for ber in BERS] for name, m, b in CONFIGS}

L = ["# Link benchmark: v1 vs v2 (simulated channel, real v2 codec)", "",
     "Frame sizes: v1 = 205 B ASCII (representative of the 44-field frame; real size unverified), v2 = 32 B binary.",
     "Mega main-loop period for command pick-up is an ASSUMED 4-40 ms and dominates command response time.", "",
     "| Configuration | Bit error rate | Delivery % | Undetected damaged/wrong frames | Latency mean ms | p95 ms | Command success % | Response mean ms | p95 ms | Mega TX stall ms/s |",
     "|---|---|---|---|---|---|---|---|---|---|"]
for name, _, _ in CONFIGS:
    for ber, r in zip(BERS, res[name]):
        L.append(f"| {name} | {ber:g} | {r['pdr_pct']:.1f} | {r['silent_wrong_or_undetected']:.0f} | {r['latency_mean_ms']:.1f} | {r['latency_p95_ms']:.1f} | "
                 f"{r['cmd_success_pct']:.1f} | {r['resp_mean_ms']:.1f} | {r['resp_p95_ms']:.1f} | {r['mega_tx_stall_ms_per_s']:.1f} |")
L += ["", "Inference (not a measurement): the thesis delivery ratio of 93 % over a 205-byte frame would correspond to a",
      f"random bit error rate of about {1 - 0.93 ** (1 / 1640):.1e} if all losses were bit errors on the wire."]
open(os.path.join(OUT, "link_benchmark.md"), "w").write("\n".join(L) + "\n")

fig, ax = plt.subplots(1, 3, figsize=(14, 4))
xs = [max(b, 1e-6) for b in BERS]
for name, _, _ in CONFIGS:
    ax[0].plot(xs, [r["pdr_pct"] for r in res[name]], "o-", label=name)
    ax[1].plot(xs, [r["latency_mean_ms"] for r in res[name]], "o-", label=name)
    ax[2].plot(xs, [r["cmd_success_pct"] for r in res[name]], "o-", label=name)
for a, t in zip(ax, ("Frames delivered intact %", "Telemetry latency, mean ms (log)", "Commands confirmed %")):
    a.set_xscale("log"); a.set_xlabel("Bit error rate (0 plotted at 1e-6)"); a.set_title(t); a.grid(alpha=.3)
ax[1].set_yscale("log"); ax[0].legend(fontsize=8)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "link_benchmark.png"), dpi=130)
print("\n".join(L))
