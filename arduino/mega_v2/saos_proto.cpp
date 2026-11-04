#include "saos_proto.h"

namespace saos { namespace proto {

uint16_t crc16(const uint8_t* d, size_t len) {
    uint16_t crc = 0xFFFF;
    for (size_t i = 0; i < len; ++i) {
        crc ^= (uint16_t)d[i] << 8;
        for (uint8_t b = 0; b < 8; ++b)
            crc = (crc & 0x8000) ? (uint16_t)((crc << 1) ^ 0x1021) : (uint16_t)(crc << 1);
    }
    return crc;
}

size_t cobs_encode(const uint8_t* in, size_t len, uint8_t* out) {
    size_t read = 0, write = 1, code_idx = 0;
    uint8_t code = 1;
    while (read < len) {
        if (in[read] == 0) {
            out[code_idx] = code; code = 1; code_idx = write++; ++read;
        } else {
            out[write++] = in[read++]; ++code;
            if (code == 0xFF) { out[code_idx] = code; code = 1; code_idx = write++; }
        }
    }
    out[code_idx] = code;
    return write;
}

int cobs_decode(const uint8_t* in, size_t len, uint8_t* out) {
    size_t read = 0, write = 0;
    while (read < len) {
        const uint8_t code = in[read];
        if (code == 0 || read + code > len) return -1;
        ++read;
        for (uint8_t i = 1; i < code; ++i) out[write++] = in[read++];
        if (code != 0xFF && read < len) out[write++] = 0;
    }
    return (int)write;
}

size_t encode(const Message& m, uint8_t* wire) {
    if (m.len > MAX_PAYLOAD) return 0;
    uint8_t raw[MAX_RAW];
    size_t n = 0;
    raw[n++] = m.type;
    raw[n++] = (uint8_t)(m.seq & 0xFF);
    raw[n++] = (uint8_t)(m.seq >> 8);
    for (uint8_t i = 0; i < m.len; ++i) raw[n++] = m.payload[i];
    const uint16_t c = crc16(raw, n);
    raw[n++] = (uint8_t)(c & 0xFF);
    raw[n++] = (uint8_t)(c >> 8);
    size_t w = cobs_encode(raw, n, wire);
    wire[w++] = 0x00;
    return w;
}

// ---- little-endian helpers ----------------------------------------------
namespace {
struct W { uint8_t* p; uint8_t n; void u8(uint8_t v){p[n++]=v;} void u16(uint16_t v){p[n++]=(uint8_t)v;p[n++]=(uint8_t)(v>>8);}
           void u32(uint32_t v){u16((uint16_t)v);u16((uint16_t)(v>>16));} };
struct R { const uint8_t* p; uint8_t n; uint8_t u8(){return p[n++];} uint16_t u16(){uint16_t v=p[n]|((uint16_t)p[n+1]<<8);n+=2;return v;}
           uint32_t u32(){uint32_t lo=u16();uint32_t hi=u16();return lo|(hi<<16);} };
}

void pack(const Telemetry& t, uint16_t seq, Message& m) {
    m.type = TELEMETRY; m.seq = seq; W w = { m.payload, 0 };
    w.u32(t.t_ms); w.u16((uint16_t)t.air_c100); w.u16((uint16_t)t.water_c100); w.u16(t.ph100); w.u16(t.tds_ppm);
    w.u16(t.level10); w.u16(t.lux); w.u16(t.batt_mv); w.u16((uint16_t)t.batt_ma10); w.u16(t.solar_w10);
    w.u8(t.relays); w.u8(t.mode); w.u8(t.valid); m.len = w.n;
}
bool unpack(const Message& m, Telemetry& t) {
    if (m.type != TELEMETRY || m.len != 25) return false;
    R r = { m.payload, 0 };
    t.t_ms = r.u32(); t.air_c100 = (int16_t)r.u16(); t.water_c100 = (int16_t)r.u16(); t.ph100 = r.u16(); t.tds_ppm = r.u16();
    t.level10 = r.u16(); t.lux = r.u16(); t.batt_mv = r.u16(); t.batt_ma10 = (int16_t)r.u16(); t.solar_w10 = r.u16();
    t.relays = r.u8(); t.mode = r.u8(); t.valid = r.u8();
    return true;
}
void pack(const Command& c, uint16_t seq, Message& m) { m.type = COMMAND; m.seq = seq; W w = { m.payload, 0 }; w.u32(c.t_tx); w.u8(c.device); w.u8(c.value); m.len = w.n; }
bool unpack(const Message& m, Command& c) { if (m.type != COMMAND || m.len != 6) return false; R r = { m.payload, 0 }; c.t_tx = r.u32(); c.device = r.u8(); c.value = r.u8(); return true; }
void pack(const Ack& a, uint16_t seq, Message& m) { m.type = ACK; m.seq = seq; W w = { m.payload, 0 }; w.u32(a.t_tx_echo); w.u8(a.device); w.u8(a.applied); w.u16(a.proc_ms); m.len = w.n; }
bool unpack(const Message& m, Ack& a) { if (m.type != ACK || m.len != 8) return false; R r = { m.payload, 0 }; a.t_tx_echo = r.u32(); a.device = r.u8(); a.applied = r.u8(); a.proc_ms = r.u16(); return true; }
void pack(const Ping& p, uint16_t seq, Message& m) { m.type = PING; m.seq = seq; W w = { m.payload, 0 }; w.u32(p.t_tx); m.len = w.n; }
bool unpack(const Message& m, Ping& p) { if (m.type != PING || m.len != 4) return false; R r = { m.payload, 0 }; p.t_tx = r.u32(); return true; }
void pack(const Pong& p, uint16_t seq, Message& m) { m.type = PONG; m.seq = seq; W w = { m.payload, 0 }; w.u32(p.t_tx_echo); w.u32(p.t_rx_ms); m.len = w.n; }
bool unpack(const Message& m, Pong& p) { if (m.type != PONG || m.len != 8) return false; R r = { m.payload, 0 }; p.t_tx_echo = r.u32(); p.t_rx_ms = r.u32(); return true; }

bool Decoder::feed(uint8_t b, Message& out) {
    if (b != 0x00) {
        if (n_ < MAX_WIRE) buf_[n_++] = b; else overflow_ = true;
        return false;
    }
    const uint8_t len = n_; const bool ovf = overflow_;
    n_ = 0; overflow_ = false;
    if (len == 0) return false;                                  // idle delimiter
    if (ovf) { ++too_long; return false; }
    uint8_t raw[MAX_WIRE];
    const int rn = cobs_decode(buf_, len, raw);
    if (rn < 0) { ++cobs_fail; return false; }
    if (rn < 5) { ++too_short; return false; }
    const uint16_t got = (uint16_t)(raw[rn - 2] | ((uint16_t)raw[rn - 1] << 8));
    if (crc16(raw, (size_t)rn - 2) != got) { ++crc_fail; return false; }
    const int plen = rn - 5;
    if (plen > MAX_PAYLOAD) { ++too_long; return false; }
    out.type = raw[0]; out.seq = (uint16_t)(raw[1] | ((uint16_t)raw[2] << 8)); out.len = (uint8_t)plen;
    for (int i = 0; i < plen; ++i) out.payload[i] = raw[3 + i];
    ++good;
    return true;
}

}}  // namespace saos::proto
