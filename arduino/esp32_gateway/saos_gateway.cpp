#include "saos_gateway.h"
#include <stdio.h>
#include <string.h>

namespace saos { namespace gw {

Gateway::Gateway(const Config& c) : cfg_(c), have_(false), seq_seen_(false), was_up_(false),
    last_seq_(0), tx_seq_(0), last_rx_ms_(0), last_tx_any_ms_(0), sent_any_(false) {
    memset(&tel_, 0, sizeof tel_);
    for (int i = 0; i < DEVICE_COUNT; ++i) {
        held_[i] = 0; last_send_ms_[i] = 0; send_due_[i] = false; wait_ack_[i] = false;
        first_tx_ms_[i] = last_tx_ms_[i] = 0; tries_[i] = 0;
    }
}

void Gateway::onByte(uint8_t b, uint32_t now_ms) {
    proto::Message m;
    if (dec_.feed(b, m)) onMessage(m, now_ms);
}

void Gateway::onMessage(const proto::Message& m, uint32_t now_ms) {
    if (m.type == proto::TELEMETRY) {
        proto::Telemetry t;
        if (!proto::unpack(m, t)) return;
        if (seq_seen_) {
            uint16_t gap = (uint16_t)(m.seq - last_seq_);       // wraps correctly at 65536
            if (gap == 0) return;                               // duplicate
            if (gap > 1 && gap < 1000) st_.telemetry_lost += (uint32_t)(gap - 1);
        }
        seq_seen_ = true; last_seq_ = m.seq; tel_ = t; have_ = true; last_rx_ms_ = now_ms;
        st_.telemetry_rx++;
        was_up_ = true;
    } else if (m.type == proto::ACK) {
        proto::Ack a;
        if (!proto::unpack(m, a) || a.device >= DEVICE_COUNT) return;
        if (wait_ack_[a.device] && a.t_tx_echo == last_tx_ms_[a.device]) {
            uint32_t resp = now_ms - first_tx_ms_[a.device];
            wait_ack_[a.device] = false;
            st_.cmd_acked++; st_.resp_sum_ms += resp;
            if (resp > st_.resp_max_ms) st_.resp_max_ms = resp;
        }
        last_rx_ms_ = now_ms;
    }
}

bool Gateway::request(Device d, bool on, uint32_t now_ms) {
    (void)now_ms;
    if (d >= DEVICE_COUNT) return false;
    uint8_t want = on ? 2 : 1;
    if (held_[d] != want) {                  // a real change: track it until ACKed
        held_[d] = want; send_due_[d] = true; st_.cmd_changes++;
        wait_ack_[d] = false; tries_[d] = 0;
    }
    return true;
}

void Gateway::release(Device d) {
    if (d >= DEVICE_COUNT) return;
    held_[d] = 0; send_due_[d] = false; wait_ack_[d] = false;
}

size_t Gateway::poll(uint32_t now_ms, uint8_t* wire, size_t cap) {
    if (cap < proto::MAX_WIRE) return 0;
    if (sent_any_ && (now_ms - last_tx_any_ms_) < cfg_.min_gap_ms) return 0;     // pace frames, see Config::min_gap_ms
    for (int i = 0; i < DEVICE_COUNT; ++i) {
        if (!held_[i]) continue;
        bool send = false;
        if (send_due_[i]) {                                           // first transmission of a change
            send = true; first_tx_ms_[i] = now_ms; tries_[i] = 0; wait_ack_[i] = true; send_due_[i] = false;
        } else if (wait_ack_[i] && (now_ms - last_tx_ms_[i]) >= cfg_.ack_timeout_ms) {
            if (tries_[i] >= cfg_.max_retries) { wait_ack_[i] = false; st_.cmd_failed++; }
            else { send = true; tries_[i]++; st_.cmd_retries++; }
        } else if ((now_ms - last_send_ms_[i]) >= cfg_.heartbeat_ms) {
            send = true;                                              // heartbeat keeps the Mega in REMOTE
        }
        if (!send) continue;
        proto::Command c; c.t_tx = now_ms; c.device = (uint8_t)i; c.value = (held_[i] == 2) ? 1 : 0;
        proto::Message m; proto::pack(c, tx_seq_++, m);
        last_send_ms_[i] = now_ms;
        if (wait_ack_[i]) last_tx_ms_[i] = now_ms;
        last_tx_any_ms_ = now_ms; sent_any_ = true;
        return proto::encode(m, wire);                                // one frame per poll; others go next call
    }
    return 0;
}

bool Gateway::linkUp(uint32_t now_ms) const {
    return have_ && (now_ms - last_rx_ms_) <= cfg_.link_timeout_ms;
}

float Gateway::pdrPercent() const {
    uint32_t tot = st_.telemetry_rx + st_.telemetry_lost;
    return tot ? 100.0f * (float)st_.telemetry_rx / (float)tot : 0.0f;
}

float Gateway::meanResponseMs() const {
    return st_.cmd_acked ? (float)st_.resp_sum_ms / (float)st_.cmd_acked : 0.0f;
}

size_t Gateway::snapshotJson(char* buf, size_t cap, uint32_t now_ms) const {
    const proto::Telemetry& t = tel_;
    int n = snprintf(buf, cap,
        "{\"link\":%s,\"age_ms\":%lu,\"air_c\":%.2f,\"water_c\":%.2f,\"ph\":%.2f,\"tds\":%u,\"level\":%.1f,"
        "\"lux\":%u,\"batt_v\":%.2f,\"batt_a\":%.2f,\"solar_w\":%.1f,\"relays\":%u,\"mode\":\"%s\","
        "\"valid\":%u,\"pdr\":%.1f,\"resp_ms\":%.0f,\"cmd_failed\":%lu}",
        linkUp(now_ms) ? "true" : "false", have_ ? (unsigned long)(now_ms - last_rx_ms_) : 0UL,
        t.air_c100 / 100.0, t.water_c100 / 100.0, t.ph100 / 100.0, (unsigned)t.tds_ppm, t.level10 / 10.0,
        (unsigned)t.lux, t.batt_mv / 1000.0, t.batt_ma10 / 10.0, t.solar_w10 / 10.0, (unsigned)t.relays,
        t.mode ? "REMOTE" : "AUTO", (unsigned)t.valid, pdrPercent(), meanResponseMs(),
        (unsigned long)st_.cmd_failed);
    return (n > 0 && (size_t)n < cap) ? (size_t)n : 0;
}

}}  // namespace saos::gw
