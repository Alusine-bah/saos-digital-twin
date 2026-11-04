// Prints the hex of one telemetry frame (same sample as test_proto) so other-language decoders can be checked byte for byte.
#include <cstdio>
#include <cstring>
#include "saos_proto.h"
using namespace saos::proto;
int main() {
    Telemetry t; std::memset(&t, 0, sizeof t);
    t.t_ms = 123456; t.air_c100 = 2987; t.water_c100 = -50; t.ph100 = 702; t.tds_ppm = 611; t.level10 = 553;
    t.batt_mv = 12840; t.batt_ma10 = -125; t.relays = 0x05; t.mode = 1; t.valid = 0x3F;
    Message m; pack(t, 4242, m); uint8_t w[MAX_WIRE]; size_t n = encode(m, w);
    for (size_t i = 0; i < n; ++i) std::printf("%02x", w[i]);
    std::printf("\n");
    return 0;
}
