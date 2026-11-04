#include <cstdio>
#include <cstring>
#include <cstdlib>
#include "saos_proto.h"
using namespace saos::proto;

static int failures = 0, checks = 0;
#define CHECK(c) do { ++checks; if (!(c)) { ++failures; std::printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

static Telemetry sampleTelemetry() {
    Telemetry t; std::memset(&t, 0, sizeof t);
    t.t_ms = 123456; t.air_c100 = 2987; t.water_c100 = -50; t.ph100 = 702; t.tds_ppm = 611; t.level10 = 553;
    t.lux = 0;                                  // zeros exercise COBS
    t.batt_mv = 12840; t.batt_ma10 = -125; t.solar_w10 = 0; t.relays = 0x05; t.mode = 1; t.valid = 0x3F;
    return t;
}

static void crc_vector() { const char* s = "123456789"; CHECK(crc16((const uint8_t*)s, 9) == 0x29B1); }

static void cobs_vectors() {
    const uint8_t a[] = {0x00}; uint8_t o[8];
    CHECK(cobs_encode(a, 1, o) == 2 && o[0] == 1 && o[1] == 1);
    const uint8_t b[] = {0x11, 0x22, 0x00, 0x33}; size_t n = cobs_encode(b, 4, o);
    const uint8_t eb[] = {0x03, 0x11, 0x22, 0x02, 0x33};
    CHECK(n == 5 && std::memcmp(o, eb, 5) == 0);
    uint8_t back[8]; CHECK(cobs_decode(o, n, back) == 4 && std::memcmp(back, b, 4) == 0);
    const uint8_t bad[] = {0x05, 0x01};   CHECK(cobs_decode(bad, 2, back) == -1);
}

static void roundtrip() {
    uint8_t wire[MAX_WIRE]; Message m, r; Decoder d;
    Telemetry t = sampleTelemetry(), t2; pack(t, 4242, m);
    size_t n = encode(m, wire); CHECK(n > 0 && wire[n - 1] == 0);
    for (size_t i = 0; i + 1 < n; ++i) CHECK(wire[i] != 0);       // no zero inside a frame
    bool got = false; for (size_t i = 0; i < n; ++i) got = d.feed(wire[i], r) || got;
    CHECK(got && r.type == TELEMETRY && r.seq == 4242 && unpack(r, t2) && std::memcmp(&t, &t2, sizeof t) == 0);
    CHECK(n == 32);                                              // 25 B payload -> 32 B on the wire

    Command c = { 99887766u, 4, 1 }, c2; pack(c, 7, m); n = encode(m, wire); got = false;
    for (size_t i = 0; i < n; ++i) got = d.feed(wire[i], r) || got;
    CHECK(got && unpack(r, c2) && c2.t_tx == c.t_tx && c2.device == 4 && c2.value == 1);

    Ack a = { 99887766u, 4, 1, 17 }, a2; pack(a, 7, m); n = encode(m, wire); got = false;
    for (size_t i = 0; i < n; ++i) got = d.feed(wire[i], r) || got;
    CHECK(got && unpack(r, a2) && a2.proc_ms == 17 && a2.t_tx_echo == a.t_tx_echo);
    CHECK(!unpack(r, c2));                                       // wrong type is rejected
}

static void resync_after_garbage() {
    uint8_t wire[MAX_WIRE]; Message m, r; Decoder d; pack(sampleTelemetry(), 1, m);
    size_t n = encode(m, wire);
    const uint8_t junk[] = {0x13, 0x77, 0xFF, 0x00, 0x05, 0x00, 0x00};
    for (uint8_t b : junk) d.feed(b, r);
    for (size_t i = 0; i + 3 < n; ++i) d.feed(wire[i], r);       // truncated frame ...
    d.feed(0x00, r);                                             // ... closed early: must be rejected
    bool got = false; for (size_t i = 0; i < n; ++i) got = d.feed(wire[i], r) || got;   // then a good one
    CHECK(got && r.seq == 1);
    CHECK(d.crc_fail + d.cobs_fail + d.too_short >= 2);
}

// Every single-bit and every double-bit error must never produce an accepted message that differs from the original.
static void exhaustive_bit_errors() {
    uint8_t wire[MAX_WIRE]; Message m, r; pack(sampleTelemetry(), 31000, m);
    const size_t n = encode(m, wire); const size_t bits = n * 8;
    size_t accepted_wrong = 0, trials = 0;
    for (size_t i = 0; i < bits; ++i) for (size_t j = i; j < bits; ++j) {
        uint8_t w[MAX_WIRE]; std::memcpy(w, wire, n);
        w[i / 8] ^= (uint8_t)(1u << (i % 8));
        if (j != i) w[j / 8] ^= (uint8_t)(1u << (j % 8));
        Decoder d; ++trials;
        for (size_t k = 0; k < n; ++k) {
            if (d.feed(w[k], r)) {
                Message ref = m;
                if (r.type != ref.type || r.seq != ref.seq || r.len != ref.len || std::memcmp(r.payload, ref.payload, r.len) != 0) ++accepted_wrong;
            }
        }
    }
    std::printf("bit-error sweep: %zu trials, %zu accepted-but-wrong\n", trials, accepted_wrong);
    CHECK(accepted_wrong == 0);
}

// Burst errors up to 16 bits are always detected by CRC-16.
static void burst_errors() {
    uint8_t wire[MAX_WIRE]; Message m, r; pack(sampleTelemetry(), 5, m);
    const size_t n = encode(m, wire); size_t wrong = 0;
    for (size_t start = 0; start + 16 <= (n - 1) * 8; ++start)
        for (uint32_t pat = 1; pat < 65536; pat += 37) {
            if (!(pat & 1) || !(pat & 0x8000)) continue;           // burst length exactly 16
            uint8_t w[MAX_WIRE]; std::memcpy(w, wire, n); Decoder d;
            for (int b = 0; b < 16; ++b) if (pat & (1u << b)) { size_t bit = start + b; w[bit / 8] ^= (uint8_t)(1u << (bit % 8)); }
            for (size_t k = 0; k < n; ++k) if (d.feed(w[k], r)) {
                if (std::memcmp(r.payload, m.payload, m.len) != 0 || r.seq != m.seq) ++wrong;
            }
        }
    CHECK(wrong == 0);
}

static void seq_wrap_and_overflow() {
    uint8_t wire[MAX_WIRE]; Message m, r; Decoder d; pack(Ping{ 1 }, 65535, m);
    size_t n = encode(m, wire); bool got = false;
    for (size_t i = 0; i < n; ++i) got = d.feed(wire[i], r) || got;
    CHECK(got && r.seq == 65535);
    for (int i = 0; i < 200; ++i) d.feed(0x55, r);               // overlong junk without delimiter
    d.feed(0x00, r); CHECK(d.too_long == 1);
    got = false; for (size_t i = 0; i < n; ++i) got = d.feed(wire[i], r) || got;
    CHECK(got);                                                  // recovers afterwards
}

int main() {
    crc_vector(); cobs_vectors(); roundtrip(); resync_after_garbage();
    exhaustive_bit_errors(); burst_errors(); seq_wrap_and_overflow();
    std::printf("%d checks, %d failures\n", checks, failures);
    return failures ? 1 : 0;
}
