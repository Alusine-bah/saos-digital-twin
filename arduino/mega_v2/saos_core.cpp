#include "saos_core.h"

namespace saos {

static inline bool isValid(real_t x) { return x == x; }          // false for NaN

Limits::Limits()
    : fan_on_c(30.0), fan_off_c(28.0),
      ph_low(6.5), ph_high(7.2), ph_ctrl_min(2.0), ph_ctrl_max(12.0),
      tds_low(600.0), tds_high(620.0),
      level_low(40.0), level_high(70.0),
      light_auto(false), photoperiod_start_h(6.0), photoperiod_end_h(18.0),
      light_on_lux(300.0), light_off_lux(500.0),
      ph_mode(PH_CONTINUOUS), ph_pulse_ms(3000), ph_wait_ms(90000),
      esp_timeout_ms(8000), min_on_ms(0), min_off_ms(0) {}

Controller::Controller(const Limits& lim)
    : lim_(lim), auto_(true), remote_active_(false), last_cmd_ms_(0), have_cmd_(false),
      ph_cool_until_ms_(0), ph_pulse_until_ms_(0) {
    for (uint8_t i = 0; i < DEVICE_COUNT; ++i) {
        st_[i] = false; toggles_[i] = 0; last_change_ms_[i] = 0; changed_once_[i] = false;
    }
}

// force = true is used for safety shut-offs, ESP32 commands and all dosing (pH, nutrient): they bypass the dwell timers.
// A minimum on-time on a dosing pump forces an overshoot (see results/tds_study.md), so dwell applies to fan, tank pump and light only.
void Controller::set(Device d, bool v, uint32_t now_ms, bool force) {
    if (st_[d] == v) return;
    if (!force && changed_once_[d]) {
        const uint32_t held = now_ms - last_change_ms_[d];
        if (st_[d]  && held < lim_.min_on_ms)  return;     // running: keep on for min_on
        if (!st_[d] && held < lim_.min_off_ms) return;     // stopped: keep off for min_off
    }
    st_[d] = v;
    ++toggles_[d];
    last_change_ms_[d] = now_ms;
    changed_once_[d] = true;
}

void Controller::espCommand(uint32_t now_ms, Device d, bool on) {
    remote_active_ = true;
    auto_ = false;
    have_cmd_ = true;
    last_cmd_ms_ = now_ms;
    if (d == PH_UP && on)   set(PH_DOWN, false, now_ms, true);   // never both dosers
    if (d == PH_DOWN && on) set(PH_UP, false, now_ms, true);
    set(d, on, now_ms, true);
}

void Controller::tick(uint32_t now_ms, const Inputs& in) {
    if (remote_active_ && have_cmd_ && (now_ms - last_cmd_ms_) > lim_.esp_timeout_ms) {
        remote_active_ = false;
        auto_ = true;
    }
    if (remote_active_ || !auto_) return;

    // exhaust fan
    if (isValid(in.air_c)) {
        if (in.air_c >= lim_.fan_on_c)       set(FAN, true, now_ms, false);
        else if (in.air_c <= lim_.fan_off_c) set(FAN, false, now_ms, false);
    } else {
        set(FAN, false, now_ms, true);               // v2: invalid air sensor -> fan off
    }

    // pH dosing
    const real_t ph = in.ph;
    const bool phValid = isValid(ph) && ph > lim_.ph_ctrl_min && ph < lim_.ph_ctrl_max;
    if (!phValid) {
        set(PH_UP, false, now_ms, true);
        set(PH_DOWN, false, now_ms, true);
    } else if (lim_.ph_mode == PH_CONTINUOUS) {
        set(PH_UP,   ph < lim_.ph_low,  now_ms, true);
        set(PH_DOWN, ph > lim_.ph_high, now_ms, true);
    } else {
        if (now_ms < ph_pulse_until_ms_) {
            // keep the current pulse running
        } else {
            set(PH_UP, false, now_ms, true);
            set(PH_DOWN, false, now_ms, true);
            if (now_ms >= ph_cool_until_ms_) {
                if (ph < lim_.ph_low)       set(PH_UP, true, now_ms, true);
                else if (ph > lim_.ph_high) set(PH_DOWN, true, now_ms, true);
                if (st_[PH_UP] || st_[PH_DOWN]) {
                    ph_pulse_until_ms_ = now_ms + lim_.ph_pulse_ms;
                    ph_cool_until_ms_  = now_ms + lim_.ph_pulse_ms + lim_.ph_wait_ms;
                }
            }
        }
    }

    // nutrient (TDS)
    if (isValid(in.tds)) {
        if (in.tds <= lim_.tds_low)       set(NUTRIENT, true, now_ms, true);
        else if (in.tds >= lim_.tds_high) set(NUTRIENT, false, now_ms, true);
    } else {
        set(NUTRIENT, false, now_ms, true);
    }

    // tank pump, evaluated whenever a fresh level sample arrives
    if (in.level_new) {
        if (isValid(in.level)) {
            if (in.level <= lim_.level_low)       set(TANK_PUMP, true, now_ms, false);
            else if (in.level >= lim_.level_high) set(TANK_PUMP, false, now_ms, false);
        } else {
            set(TANK_PUMP, false, now_ms, true);     // v2: no level reading -> do not run dry
        }
    }

    // grow light (v1 had none)
    if (lim_.light_auto) {
        const bool inWindow = in.hour >= lim_.photoperiod_start_h && in.hour < lim_.photoperiod_end_h;
        if (inWindow && in.lux < lim_.light_on_lux)            set(LIGHT, true, now_ms, false);
        else if (!inWindow || in.lux > lim_.light_off_lux)     set(LIGHT, false, now_ms, false);
    }
}

}  // namespace saos
