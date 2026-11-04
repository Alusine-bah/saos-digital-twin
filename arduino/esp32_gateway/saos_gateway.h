// SAOS v2 ESP32 gateway core.  Pure C++11, no heap/STL, no Arduino calls: runs on the ESP32 and on a PC.
//
// Design rules (fixing what the v1 audit found):
//   * The Mega is the single control authority. The gateway never decides on its own; it only relays operator
//     requests and shows state. (v1 had a second set of limits in the ESP32 that disagreed with the Mega.)
//   * Operator requests are "held": the gateway re-sends them every heartbeat so the Mega's 8 s remote watchdog
//     never expires while the operator wants manual control. release() stops the heartbeat; the Mega then
//     returns to AUTO by itself after its timeout.
//   * A changed request is tracked until the Mega ACKs it (retry, then give up and report failure).
//   * Everything time-related takes `now_ms` from the caller, so tests are deterministic.
#ifndef SAOS_GATEWAY_H
#define SAOS_GATEWAY_H

#include <stdint.h>
#include <stddef.h>
#include "saos_core.h"
#include "saos_proto.h"

namespace saos { namespace gw {

struct Config {
    uint32_t heartbeat_ms;     // resend period for held commands (must be well below the Mega's 8000 ms watchdog)
    uint32_t ack_timeout_ms;   // wait before retrying a changed command
    uint8_t  max_retries;
    uint32_t link_timeout_ms;  // no valid frame for this long -> link down
    uint32_t min_gap_ms;       // minimum time between two transmitted frames: stops command bursts that could overrun the Mega's 64-byte RX buffer
    Config() : heartbeat_ms(2000), ack_timeout_ms(300), max_retries(3), link_timeout_ms(3000), min_gap_ms(20) {}
};

struct Stats {
    uint32_t telemetry_rx, telemetry_lost;     // lost = sequence gaps
    uint32_t cmd_changes, cmd_acked, cmd_failed, cmd_retries;
    uint32_t resp_sum_ms, resp_max_ms;         // first send -> ACK received, for acked changes
    uint32_t link_down_events;
    Stats() { telemetry_rx = telemetry_lost = cmd_changes = cmd_acked = cmd_failed = cmd_retries = 0;
              resp_sum_ms = resp_max_ms = link_down_events = 0; }
};

class Gateway {
public:
    explicit Gateway(const Config& c = Config());

    void onByte(uint8_t b, uint32_t now_ms);                      // feed bytes arriving from the Mega
    bool request(Device d, bool on, uint32_t now_ms);              // operator wants d forced to `on`
    void release(Device d);                                        // operator gives control back
    size_t poll(uint32_t now_ms, uint8_t* wire, size_t cap);       // bytes to send now (0 or one frame)

    bool linkUp(uint32_t now_ms) const;
    bool haveTelemetry() const { return have_; }
    const proto::Telemetry& last() const { return tel_; }
    const Stats& stats() const { return st_; }
    const proto::Decoder& decoder() const { return dec_; }
    bool held(Device d) const { return held_[d] != 0; }
    float pdrPercent() const;                                      // delivery ratio from sequence gaps
    float meanResponseMs() const;
    // Dashboard snapshot as JSON (fixed schema). Returns bytes written (without NUL), 0 if it does not fit.
    size_t snapshotJson(char* buf, size_t cap, uint32_t now_ms) const;

private:
    Config cfg_;
    proto::Decoder dec_;
    proto::Telemetry tel_;
    Stats st_;
    bool have_, seq_seen_, was_up_;
    uint16_t last_seq_, tx_seq_;
    uint32_t last_rx_ms_, last_tx_any_ms_;
    bool     sent_any_;
    uint8_t  held_[DEVICE_COUNT];          // 0 none, 1 hold OFF, 2 hold ON
    uint32_t last_send_ms_[DEVICE_COUNT];
    bool     send_due_[DEVICE_COUNT];      // a changed request not yet sent
    // tracking of the single most recent changed command per device
    bool     wait_ack_[DEVICE_COUNT];
    uint32_t first_tx_ms_[DEVICE_COUNT], last_tx_ms_[DEVICE_COUNT];
    uint8_t  tries_[DEVICE_COUNT];
    void onMessage(const proto::Message& m, uint32_t now_ms);
};

}}  // namespace saos::gw
#endif
