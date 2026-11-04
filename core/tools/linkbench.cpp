// Link benchmark: v1 (ASCII, 9600 baud, no integrity check) vs v2 (binary, CRC, sequence numbers, retries).
// Uses the real v2 encoder/decoder; the channel (serialization time, byte loss, bit errors) is simulated.
// usage: linkbench mode=v1|v2 baud=115200 hz=1 ber=0 byteloss=0 seconds=3600 seed=1 cmd_s=10 v1_bytes=205
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <random>
#include <string>
#include <vector>
#include "saos_proto.h"
using namespace saos::proto;

struct Cfg {
    std::string mode = "v2"; double baud = 115200, hz = 1, ber = 0, byteloss = 0, seconds = 3600, cmd_s = 10;
    unsigned seed = 1; int v1_bytes = 205, v1_cmd_bytes = 22;
    double rx_jit_lo = 0.3, rx_jit_hi = 1.2;      // [ASSUMED] ESP32/Mega UART polling delay, ms
    double loop_lo = 4.0, loop_hi = 40.0;         // [ASSUMED] Mega main-loop period incl. LCD, ms
    double timeout_ms = 150; int max_tries = 4;
    int tx_buf = 64;                              // Arduino HardwareSerial TX buffer
} cfg;

static std::mt19937_64 rng;
static double U(double a, double b) { return std::uniform_real_distribution<double>(a, b)(rng); }
static double R() { return U(0, 1); }

// returns damaged flag; bytes may be dropped or have bits flipped
static bool corrupt(std::vector<uint8_t>& v) {
    bool dmg = false; std::vector<uint8_t> o; o.reserve(v.size());
    for (uint8_t b : v) {
        if (cfg.byteloss > 0 && R() < cfg.byteloss) { dmg = true; continue; }
        if (cfg.ber > 0) for (int i = 0; i < 8; ++i) if (R() < cfg.ber) { b ^= (uint8_t)(1u << i); dmg = true; }
        o.push_back(b);
    }
    v.swap(o); return dmg;
}
static double ser_ms(size_t bytes) { return bytes * 10.0 / cfg.baud * 1000.0; }
static double pct(std::vector<double> a, double q) { if (a.empty()) return NAN; std::sort(a.begin(), a.end()); return a[std::min(a.size() - 1, (size_t)(q * a.size()))]; }
static double mean(const std::vector<double>& a) { if (a.empty()) return NAN; double s = 0; for (double x : a) s += x; return s / a.size(); }
static double mx(const std::vector<double>& a) { return a.empty() ? NAN : *std::max_element(a.begin(), a.end()); }

static bool same(const Message& a, const Message& b) { return a.type == b.type && a.seq == b.seq && a.len == b.len && !std::memcmp(a.payload, b.payload, a.len); }

int main(int argc, char** argv) {
    for (int i = 1; i < argc; ++i) {
        std::string a = argv[i]; size_t e = a.find('='); if (e == std::string::npos) return 2;
        std::string k = a.substr(0, e), v = a.substr(e + 1);
        if (k == "mode") cfg.mode = v; else if (k == "baud") cfg.baud = atof(v.c_str()); else if (k == "hz") cfg.hz = atof(v.c_str());
        else if (k == "ber") cfg.ber = atof(v.c_str()); else if (k == "byteloss") cfg.byteloss = atof(v.c_str());
        else if (k == "seconds") cfg.seconds = atof(v.c_str()); else if (k == "seed") cfg.seed = (unsigned)atoi(v.c_str());
        else if (k == "cmd_s") cfg.cmd_s = atof(v.c_str()); else if (k == "v1_bytes") cfg.v1_bytes = atoi(v.c_str());
        else { std::fprintf(stderr, "unknown %s\n", k.c_str()); return 2; }
    }
    rng.seed(cfg.seed);
    const bool v2 = cfg.mode == "v2";
    const size_t N = (size_t)(cfg.seconds * cfg.hz);

    // ---------------- telemetry stream (Mega -> ESP32) ----------------
    std::vector<double> lat; double tx_free = 0, stall_total = 0, busy = 0;
    size_t delivered = 0, silent = 0, damaged_frames = 0, wire_bytes_total = 0;
    Decoder dec;
    for (size_t k = 0; k < N; ++k) {
        const double sched = k * 1000.0 / cfg.hz;
        std::vector<uint8_t> wire; Message sent;
        if (v2) {
            Telemetry t; std::memset(&t, 0, sizeof t);
            t.t_ms = (uint32_t)sched; t.air_c100 = (int16_t)(2800 + (k % 400)); t.water_c100 = 2650; t.ph100 = (uint16_t)(650 + k % 70);
            t.tds_ppm = (uint16_t)(600 + k % 20); t.level10 = (uint16_t)(400 + k % 300); t.lux = (uint16_t)(k * 7 % 900); t.batt_mv = 12600;
            t.batt_ma10 = -80; t.solar_w10 = (uint16_t)(k % 500); t.relays = (uint8_t)(k & 0x3F); t.mode = 0; t.valid = 0x3F;
            pack(t, (uint16_t)(k & 0xFFFF), sent);
            uint8_t w[MAX_WIRE]; size_t n = encode(sent, w); wire.assign(w, w + n);
        } else {
            wire.assign((size_t)cfg.v1_bytes, 'x');
        }
        const size_t len = wire.size(); wire_bytes_total += len;
        const double start = std::max(sched, tx_free), ser = ser_ms(len);
        tx_free = start + ser; busy += ser;
        stall_total += std::max(0.0, (double)((int)len - cfg.tx_buf)) * 10.0 / cfg.baud * 1000.0;
        const bool dmg = corrupt(wire);
        if (v2) {
            Message r; bool got = false;
            for (uint8_t b : wire) if (dec.feed(b, r)) { got = true; if (same(r, sent)) { ++delivered; lat.push_back(start + ser + U(cfg.rx_jit_lo, cfg.rx_jit_hi) - sched); } else ++silent; }
            (void)got;
        } else {
            if (dmg) ++damaged_frames; else { ++delivered; lat.push_back(start + ser + U(cfg.rx_jit_lo, cfg.rx_jit_hi) - sched); }
        }
    }
    const double stall_per_s = stall_total / cfg.seconds;      // ms blocked per second of run
    const double stall_per_frame = stall_total / (double)N;

    // ---------------- commands (ESP32 -> Mega -> ACK) ----------------
    std::vector<double> resp, rtt1; size_t cmds = 0, ok = 0, tries_total = 0, dup_apply = 0, v1_damaged_cmd = 0, v1_unconfirmed = 0;
    Decoder decMega, decEsp; uint16_t cseq = 0;
    for (double tc = cfg.cmd_s * 1000.0; tc < cfg.seconds * 1000.0; tc += cfg.cmd_s * 1000.0) {
        ++cmds; bool done = false, applied_once = false; double t_first = tc, t_send = tc;
        const int tries = v2 ? cfg.max_tries : 1;
        for (int a = 0; a < tries && !done; ++a) {
            ++tries_total;
            const double poll = U(cfg.loop_lo, cfg.loop_hi) + ((R() < stall_per_frame * cfg.hz / 1000.0) ? U(0, std::max(stall_per_frame, 0.0)) : 0.0);
            if (v2) {
                Message cm; Command c = { (uint32_t)t_send, 4, (uint8_t)(cseq & 1) }; pack(c, cseq, cm);
                uint8_t w[MAX_WIRE]; size_t n = encode(cm, w); std::vector<uint8_t> wire(w, w + n);
                const double s1 = ser_ms(n); corrupt(wire); Message r; bool got = false;
                for (uint8_t b : wire) if (decMega.feed(b, r) && same(r, cm)) got = true;
                if (got) {
                    if (applied_once) { ++dup_apply; }
                    applied_once = true;
                    const double applied = t_send + s1 + U(cfg.rx_jit_lo, cfg.rx_jit_hi) + poll;
                    Message am; Ack ak = { (uint32_t)t_send, 4, c.value, (uint16_t)(poll + 0.5) }; pack(ak, cseq, am);
                    uint8_t w2[MAX_WIRE]; size_t n2 = encode(am, w2); std::vector<uint8_t> wire2(w2, w2 + n2);
                    const double s2 = ser_ms(n2); corrupt(wire2); bool got2 = false;
                    for (uint8_t b : wire2) if (decEsp.feed(b, r) && same(r, am)) got2 = true;
                    if (got2) { const double t_done = applied + s2 + U(cfg.rx_jit_lo, cfg.rx_jit_hi); resp.push_back(t_done - t_first); if (a == 0) rtt1.push_back(t_done - t_first); done = true; }
                }
                t_send += cfg.timeout_ms;
            } else {
                std::vector<uint8_t> c1((size_t)cfg.v1_cmd_bytes, 'c'), c2((size_t)cfg.v1_cmd_bytes, 'a');
                const double s1 = ser_ms(c1.size()), s2 = ser_ms(c2.size());
                const bool d1 = corrupt(c1), d2 = corrupt(c2);
                if (d1) ++v1_damaged_cmd; else if (d2) ++v1_unconfirmed;
                if (!d1 && !d2) { resp.push_back(s1 + U(cfg.rx_jit_lo, cfg.rx_jit_hi) + poll + s2 + U(cfg.rx_jit_lo, cfg.rx_jit_hi)); done = true; }
            }
            ++cseq;
        }
        if (done) ++ok;
    }

    std::printf("mode=%s\nbaud=%.0f\nber=%g\nbyteloss=%g\nframes_sent=%zu\nwire_bytes_per_frame=%.1f\n", cfg.mode.c_str(), cfg.baud, cfg.ber, cfg.byteloss, N, (double)wire_bytes_total / N);
    std::printf("frames_delivered_intact=%zu\npdr_pct=%.3f\n", delivered, 100.0 * delivered / N);
    std::printf("rejected_by_decoder=%u\nsilent_wrong_or_undetected=%zu\n", v2 ? dec.crc_fail + dec.cobs_fail + dec.too_long + dec.too_short : 0u, v2 ? silent : damaged_frames);
    std::printf("latency_mean_ms=%.2f\nlatency_p95_ms=%.2f\nlatency_max_ms=%.2f\n", mean(lat), pct(lat, 0.95), mx(lat));
    std::printf("link_utilisation_pct=%.2f\nmega_tx_stall_ms_per_s=%.2f\n", 100.0 * busy / (cfg.seconds * 1000.0), stall_per_s);
    std::printf("commands=%zu\ncmd_success_pct=%.2f\navg_tries_per_cmd=%.3f\n", cmds, cmds ? 100.0 * ok / cmds : 0.0, cmds ? (double)tries_total / cmds : 0.0);
    std::printf("resp_mean_ms=%.2f\nresp_p95_ms=%.2f\nresp_max_ms=%.2f\n", mean(resp), pct(resp, 0.95), mx(resp));
    std::printf("duplicate_applies=%zu\nv1_damaged_cmds=%zu\nv1_unconfirmed=%zu\n", dup_apply, v1_damaged_cmd, v1_unconfirmed);
    return 0;
}
