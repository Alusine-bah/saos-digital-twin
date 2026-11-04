#include <cstdio>
#include <cstring>
#include "saos_gateway.h"
using namespace saos; using namespace saos::gw;

static int failures = 0, checks = 0;
#define CHECK(c) do { ++checks; if (!(c)) { ++failures; std::printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

static void feedTel(Gateway& g, uint16_t seq, uint32_t now, uint8_t mode = 0) {
    proto::Telemetry t; std::memset(&t, 0, sizeof t); t.air_c100 = 2950; t.ph100 = 702; t.tds_ppm = 610;
    t.level10 = 550; t.batt_mv = 12800; t.mode = mode; t.valid = 0x3F;
    proto::Message m; proto::pack(t, seq, m); uint8_t w[proto::MAX_WIRE]; size_t n = proto::encode(m, w);
    for (size_t i = 0; i < n; ++i) g.onByte(w[i], now);
}
// decode what the gateway transmitted, as the Mega would
static bool decodeCmd(const uint8_t* w, size_t n, proto::Command& c) {
    proto::Decoder d; proto::Message m; bool ok = false;
    for (size_t i = 0; i < n; ++i) ok = d.feed(w[i], m) || ok;
    return ok && m.type == proto::COMMAND && proto::unpack(m, c);
}
static void feedAck(Gateway& g, const proto::Command& c, uint32_t now) {
    proto::Ack a = { c.t_tx, c.device, c.value, 5 }; proto::Message m; proto::pack(a, 1, m);
    uint8_t w[proto::MAX_WIRE]; size_t n = proto::encode(m, w); for (size_t i = 0; i < n; ++i) g.onByte(w[i], now);
}

static void telemetry_and_pdr() {
    Gateway g; uint8_t w[proto::MAX_WIRE];
    CHECK(!g.linkUp(0) && !g.haveTelemetry());
    feedTel(g, 10, 1000); feedTel(g, 11, 2000); feedTel(g, 14, 5000);          // 12, 13 lost
    CHECK(g.stats().telemetry_rx == 3 && g.stats().telemetry_lost == 2);
    CHECK(g.pdrPercent() > 59.9f && g.pdrPercent() < 60.1f);
    feedTel(g, 14, 5100); CHECK(g.stats().telemetry_rx == 3);                  // duplicate ignored
    CHECK(g.linkUp(6000) && !g.linkUp(9000));                                  // 3 s timeout
    CHECK(g.poll(6000, w, sizeof w) == 0);                                     // nothing requested -> silent
    Gateway h; feedTel(h, 65534, 0); feedTel(h, 65535, 1); feedTel(h, 0, 2); feedTel(h, 1, 3);
    CHECK(h.stats().telemetry_lost == 0 && h.stats().telemetry_rx == 4);       // wraparound
}

static void command_ack_and_response() {
    Gateway g; uint8_t w[proto::MAX_WIRE]; proto::Command c;
    CHECK(g.request(FAN, true, 100));
    size_t n = g.poll(100, w, sizeof w); CHECK(n > 0 && decodeCmd(w, n, c) && c.device == FAN && c.value == 1);
    CHECK(g.poll(150, w, sizeof w) == 0);                                      // not due yet
    feedAck(g, c, 140);
    CHECK(g.stats().cmd_acked == 1 && g.stats().resp_max_ms == 40 && g.meanResponseMs() > 39.9f);
    feedAck(g, c, 150); CHECK(g.stats().cmd_acked == 1);                       // duplicate ACK ignored
}

static void retry_then_fail() {
    Gateway g; uint8_t w[proto::MAX_WIRE];
    g.request(PH_UP, true, 0); CHECK(g.poll(0, w, sizeof w) > 0);
    int sent = 0; for (uint32_t t = 1; t <= 2000; ++t) if (g.poll(t, w, sizeof w) > 0) ++sent;
    CHECK(g.stats().cmd_retries == 3 && g.stats().cmd_failed == 1);
    CHECK(sent >= 3);
    CHECK(g.held(PH_UP));                                                      // still held; heartbeat continues
}

static void heartbeat_keeps_mega_remote() {
    Gateway g; uint8_t w[proto::MAX_WIRE]; proto::Command c;
    g.request(LIGHT, true, 0); size_t n = g.poll(0, w, sizeof w); decodeCmd(w, n, c); feedAck(g, c, 5);
    uint32_t last = 0, maxgap = 0, beats = 0;
    for (uint32_t t = 1; t <= 60000; ++t) if ((n = g.poll(t, w, sizeof w)) > 0) {
        beats++; if (t - last > maxgap) maxgap = t - last; last = t; }
    CHECK(maxgap <= 2000 && maxgap < 8000 && beats >= 29);                     // far below the Mega's 8 s watchdog
    g.release(LIGHT); CHECK(!g.held(LIGHT));
    for (uint32_t t = 60001; t <= 70000; ++t) CHECK(g.poll(t, w, sizeof w) == 0);   // silence -> Mega returns to AUTO
}

static void multiple_devices_one_frame_per_poll() {
    Gateway g; uint8_t w[proto::MAX_WIRE]; proto::Command c; bool seen[DEVICE_COUNT] = {false};
    g.request(FAN, true, 0); g.request(TANK_PUMP, false, 0); g.request(NUTRIENT, true, 0);
    size_t n = g.poll(0, w, sizeof w); CHECK(n > 0 && decodeCmd(w, n, c)); seen[c.device] = true;
    CHECK(g.poll(5, w, sizeof w) == 0);                                        // paced: no second frame within min_gap_ms (20 ms)
    for (int i = 1; i < 3; ++i) { n = g.poll(20u * i, w, sizeof w); CHECK(n > 0 && decodeCmd(w, n, c)); seen[c.device] = true; }
    CHECK(seen[FAN] && seen[TANK_PUMP] && seen[NUTRIENT]);
    CHECK(g.poll(60, w, sizeof w) == 0);
    CHECK(!g.request((Device)9, true, 0));
}


static void bursts_stay_below_rx_buffer() {
    // 6 devices held at once; any window of 16 ms (the 64-byte RX buffer drain time at 38400 baud is 16.7 ms) must carry at most 64 bytes
    Gateway g; uint8_t w[proto::MAX_WIRE]; uint32_t t_tx[2000]; size_t b_tx[2000]; int n_tx = 0;
    for (int d = 0; d < DEVICE_COUNT; ++d) g.request((Device)d, true, 0);
    for (uint32_t t = 0; t <= 20000; ++t) { size_t n = g.poll(t, w, sizeof w); if (n && n_tx < 2000) { t_tx[n_tx] = t; b_tx[n_tx++] = n; } }
    size_t worst = 0;
    for (int i = 0; i < n_tx; ++i) { size_t sum = 0; for (int j = i; j < n_tx && t_tx[j] - t_tx[i] < 16; ++j) sum += b_tx[j]; if (sum > worst) worst = sum; }
    CHECK(n_tx > 6 && worst <= 64);
}

static void json_snapshot() {
    Gateway g; char buf[400]; feedTel(g, 1, 1000, 1);
    size_t n = g.snapshotJson(buf, sizeof buf, 1500);
    CHECK(n > 0 && std::strstr(buf, "\"link\":true") && std::strstr(buf, "\"ph\":7.02") &&
          std::strstr(buf, "\"mode\":\"REMOTE\"") && std::strstr(buf, "\"tds\":610"));
    char tiny[20]; CHECK(g.snapshotJson(tiny, sizeof tiny, 1500) == 0);        // does not overrun
}

static void survives_noise_and_garbage() {
    Gateway g; feedTel(g, 1, 0);
    for (int i = 0; i < 500; ++i) g.onByte((uint8_t)(i * 37 + 11), 10);       // line noise
    g.onByte(0, 10); feedTel(g, 2, 20);
    CHECK(g.stats().telemetry_rx == 2 && g.stats().telemetry_lost == 0);
}

int main() {
    telemetry_and_pdr(); command_ack_and_response(); retry_then_fail(); heartbeat_keeps_mega_remote();
    multiple_devices_one_frame_per_poll(); bursts_stay_below_rx_buffer(); json_snapshot(); survives_noise_and_garbage();
    std::printf("%d checks, %d failures\n", checks, failures);
    return failures ? 1 : 0;
}
