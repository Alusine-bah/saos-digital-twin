// Gateway -> lossy byte link -> Mega controller (protocol decoder + Controller). Deterministic.
#include <cstdio>
#include <cstdlib>
#include "saos_gateway.h"
using namespace saos; using namespace saos::gw;
static int failures = 0, checks = 0;
#define CHECK(c) do { ++checks; if (!(c)) { ++failures; std::printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

struct MegaSide {                      // what the Mega firmware v2 will do with received bytes
    Controller ctl; proto::Decoder dec; uint16_t seq;
    MegaSide() : ctl(Limits()), seq(0) {}
    void rx(uint8_t b, uint32_t now, uint8_t* ack, size_t& acklen) {
        proto::Message m; acklen = 0;
        if (!dec.feed(b, m) || m.type != proto::COMMAND) return;
        proto::Command c; if (!proto::unpack(m, c) || c.device >= DEVICE_COUNT) return;
        ctl.espCommand(now, (Device)c.device, c.value != 0);
        proto::Ack a = { c.t_tx, c.device, c.value, 1 }; proto::Message r; proto::pack(a, seq++, r);
        acklen = proto::encode(r, ack);
    }
};

// returns bytes after dropping/corrupting a share of whole frames (loss in %)
static bool lossy(unsigned& rng, int loss_pct) { rng = rng * 1103515245u + 12345u; return (int)((rng >> 16) % 100) < loss_pct; }

static void run(int loss_pct, int& acked, int& failed, bool& auto_back, bool& remote_held) {
    Gateway g; MegaSide mega; unsigned rng = 42; uint8_t w[proto::MAX_WIRE], ack[proto::MAX_WIRE]; size_t al;
    Inputs in = {}; in.air_c = 25; in.ph = 7.0f; in.tds = 610; in.level = 55; in.level_new = false; in.hour = 12; in.lux = 1000;
    g.request(FAN, true, 0);                                                    // operator forces the fan on at t=0
    bool remote_ok = true;
    for (uint32_t t = 0; t <= 60000; ++t) {
        if (t == 30000) g.release(FAN);                                         // operator lets go at 30 s
        size_t n = g.poll(t, w, sizeof w);
        if (n && !lossy(rng, loss_pct))
            for (size_t i = 0; i < n; ++i) { mega.rx(w[i], t, ack, al);
                if (al && !lossy(rng, loss_pct)) for (size_t k = 0; k < al; ++k) g.onByte(ack[k], t); }
        if (t % 1000 == 0) {
            mega.ctl.tick(t, in);
            if (t > 2000 && t < 30000 && !(mega.ctl.get(FAN) && !mega.ctl.autoActive())) remote_ok = false;
        }
    }
    acked = (int)g.stats().cmd_acked; failed = (int)g.stats().cmd_failed;
    auto_back = mega.ctl.autoActive() && !mega.ctl.get(FAN);                    // 25 C < 28 C -> fan off in AUTO
    remote_held = remote_ok;
}

int main() {
    int acked, failed; bool back, held;
    run(0, acked, failed, back, held);   CHECK(acked == 1 && failed == 0 && back && held);
    run(20, acked, failed, back, held);  CHECK(held && back);                    // 20 % frame loss each way: fan still held, AUTO restored
    run(40, acked, failed, back, held);  CHECK(back);                            // heavy loss: AUTO still restored after release
    std::printf("%d checks, %d failures\n", checks, failures);
    return failures ? 1 : 0;
}
