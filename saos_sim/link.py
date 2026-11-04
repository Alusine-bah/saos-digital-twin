"""Mega <-> ESP32 UART link model: 44-field frame, latency, loss, command RTT."""
import random
import statistics
from .config import Params

FIELDS = 44


def build_frame(s: dict, st: dict, t: float) -> str:
    """Representative `<f0..f43>` telemetry frame (field order is NOT the real one)."""
    vals = [f"{t:.0f}", f"{s['air_c']:.1f}", f"{s['air_c']:.1f}", f"{s['water_c']:.2f}",
            f"{s['ph']:.2f}", f"{s['tds']:.0f}", f"{s['level']:.1f}", f"{s['lux']:.0f}",
            f"{s['pressure']:.1f}", f"{s['do_mgl']:.2f}", f"{s['soc_pct']:.0f}"]
    vals += [str(int(v)) for v in st.values()]
    vals += ["0.00"] * (FIELDS - len(vals))
    return "<" + ",".join(vals) + ">\n"


def serialization_ms(nbytes: int, baud: int) -> float:
    return nbytes * 10.0 / baud * 1000.0       # 8N1 -> 10 bit/byte


class Link:
    def __init__(self, p: Params, seed: int = 11):
        self.p = p
        self.rng = random.Random(seed)
        self.sent = 0
        self.received = 0
        self.lat_ms = []
        self.resp_ms = []
        self.frame_bytes = []

    def send_telemetry(self, frame: str):
        self.sent += 1
        n = len(frame)
        self.frame_bytes.append(n)
        lost = self.rng.random() < self.p.frame_loss or n > self.p.packet_buffer
        if lost:
            return False
        self.received += 1
        # Mega->ESP latency: serialization + ESP32 UART poll (0-1 ms) + parse
        self.lat_ms.append(serialization_ms(n, self.p.baud) + self.rng.uniform(0.3, 1.2))
        return True

    def command_response_ms(self) -> float:
        """Dashboard click -> relay switched on the Mega."""
        http = self.rng.uniform(*self.p.esp_http_ms)
        cmd_bytes = len("<CTRL,EXHAUST_FAN,ON>\n")
        ser = serialization_ms(cmd_bytes, self.p.baud)
        mega_poll = self.rng.uniform(*self.p.mega_loop_ms)   # waits for loop to reach Serial2 parse
        r = http + ser + mega_poll
        self.resp_ms.append(r)
        return r

    def summary(self) -> dict:
        def pct(a, q):
            a = sorted(a)
            return a[min(len(a) - 1, int(q * len(a)))] if a else float("nan")
        return dict(
            frames_sent=self.sent,
            pdr_pct=100.0 * self.received / max(self.sent, 1),
            frame_bytes_mean=statistics.mean(self.frame_bytes) if self.frame_bytes else 0,
            latency_mean_ms=statistics.mean(self.lat_ms) if self.lat_ms else float("nan"),
            latency_p95_ms=pct(self.lat_ms, 0.95),
            latency_max_ms=max(self.lat_ms) if self.lat_ms else float("nan"),
            resp_mean_ms=statistics.mean(self.resp_ms) if self.resp_ms else float("nan"),
            resp_p95_ms=pct(self.resp_ms, 0.95),
        )
