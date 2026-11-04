// SAOS v2 link protocol.  Pure C++11, no heap/STL (AVR-safe).
//
// Wire format (one frame):  COBS( type | seq_lo seq_hi | payload... | crc_lo crc_hi ) 0x00
//   * COBS framing: 0x00 never appears inside a frame, so the receiver can always resync.
//   * CRC-16/CCITT-FALSE over type..payload (check value of "123456789" is 0x29B1).
//   * seq: per-sender counter; gaps reveal lost frames (delivery ratio is computed from them).
//   * All integers little-endian, fixed point (no floats on the wire).
#ifndef SAOS_PROTO_H
#define SAOS_PROTO_H

#include <stdint.h>
#include <stddef.h>

namespace saos { namespace proto {

enum MsgType : uint8_t { TELEMETRY = 1, COMMAND = 2, ACK = 3, PING = 4, PONG = 5 };

static const uint8_t MAX_PAYLOAD = 40;
static const uint8_t MAX_RAW  = 1 + 2 + MAX_PAYLOAD + 2;
static const uint8_t MAX_WIRE = MAX_RAW + 3;          // COBS overhead + delimiter

struct Message {
    uint8_t  type;
    uint16_t seq;
    uint8_t  len;
    uint8_t  payload[MAX_PAYLOAD];
};

uint16_t crc16(const uint8_t* data, size_t len);
size_t   cobs_encode(const uint8_t* in, size_t len, uint8_t* out);     // returns bytes written
int      cobs_decode(const uint8_t* in, size_t len, uint8_t* out);     // returns bytes, or -1
size_t   encode(const Message& m, uint8_t* wire);                      // returns wire bytes incl. 0x00, 0 on error

// ---- typed payloads ----------------------------------------------------
struct Telemetry {                // 25 bytes
    uint32_t t_ms;                // sender clock
    int16_t  air_c100, water_c100;
    uint16_t ph100, tds_ppm, level10, lux;
    uint16_t batt_mv;  int16_t batt_ma10;  uint16_t solar_w10;
    uint8_t  relays;              // bit i = Device i (see saos_core.h)
    uint8_t  mode;                // 0 AUTO, 1 REMOTE
    uint8_t  valid;               // bit0 air, bit1 water, bit2 pH, bit3 TDS, bit4 level, bit5 battery
};
struct Command { uint32_t t_tx; uint8_t device, value; };               // ESP32 -> Mega
struct Ack     { uint32_t t_tx_echo; uint8_t device, applied; uint16_t proc_ms; };
struct Ping    { uint32_t t_tx; };
struct Pong    { uint32_t t_tx_echo; uint32_t t_rx_ms; };

void pack(const Telemetry&, uint16_t seq, Message& m);
void pack(const Command&,   uint16_t seq, Message& m);
void pack(const Ack&,       uint16_t seq, Message& m);
void pack(const Ping&,      uint16_t seq, Message& m);
void pack(const Pong&,      uint16_t seq, Message& m);
bool unpack(const Message&, Telemetry&);
bool unpack(const Message&, Command&);
bool unpack(const Message&, Ack&);
bool unpack(const Message&, Ping&);
bool unpack(const Message&, Pong&);

// Byte-stream decoder. feed() returns true when a complete, CRC-valid message is available in `out`.
class Decoder {
public:
    Decoder() : crc_fail(0), cobs_fail(0), too_long(0), too_short(0), good(0), n_(0), overflow_(false) {}
    bool feed(uint8_t b, Message& out);
    uint32_t crc_fail, cobs_fail, too_long, too_short, good;
private:
    uint8_t  buf_[MAX_WIRE + 4];
    uint8_t  n_;
    bool     overflow_;
};

}}  // namespace saos::proto
#endif
