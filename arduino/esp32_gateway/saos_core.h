// SAOS v2 portable control core.
// Pure C++11: no Arduino calls, no heap, no STL, no exceptions, so the same
// file builds with avr-gcc for the Mega and with g++ for host tests.
#ifndef SAOS_CORE_H
#define SAOS_CORE_H

#include <stdint.h>

#ifdef SAOS_REAL_FLOAT
typedef float real_t;          // AVR build: double == float anyway
#else
typedef double real_t;         // host build: exact parity with the Python twin
#endif

namespace saos {

enum Device : uint8_t { FAN = 0, PH_UP, PH_DOWN, NUTRIENT, LIGHT, TANK_PUMP, DEVICE_COUNT };

enum PhMode : uint8_t { PH_CONTINUOUS = 0, PH_PULSE = 1 };

// Every field is a design parameter. The defaults reproduce the v1 firmware
// (Config.h of SAOS_Mega_V_9_0_0) so the Python twin can be used as a
// parity reference. v2 values are set by the caller.
struct Limits {
    real_t fan_on_c, fan_off_c;
    real_t ph_low, ph_high, ph_ctrl_min, ph_ctrl_max;
    real_t tds_low, tds_high;
    real_t level_low, level_high;
    bool   light_auto;
    real_t photoperiod_start_h, photoperiod_end_h;
    real_t light_on_lux, light_off_lux;          // lux override inside the photoperiod
    uint8_t ph_mode;
    uint32_t ph_pulse_ms, ph_wait_ms;
    uint32_t esp_timeout_ms;
    uint32_t min_on_ms, min_off_ms;              // anti short-cycle (0 = v1 behaviour)

    Limits();                                    // v1 defaults
};

struct Inputs {
    real_t air_c;        // NaN allowed = invalid
    real_t ph;           // NaN allowed = invalid
    real_t tds;
    real_t level;        // percent
    bool   level_new;    // true when the level sensor produced a fresh sample
    real_t hour;         // 0..24 from the RTC
    real_t lux;
};

class Controller {
public:
    explicit Controller(const Limits& lim);

    // One control step; call at 1 Hz (level_new gates the tank pump).
    void tick(uint32_t now_ms, const Inputs& in);

    // ESP32 override: suspends AUTO until esp_timeout_ms passes without a command.
    void espCommand(uint32_t now_ms, Device d, bool on);

    bool     get(Device d) const { return st_[d]; }
    uint32_t toggles(Device d) const { return toggles_[d]; }
    bool     autoActive() const { return auto_; }

private:
    void set(Device d, bool v, uint32_t now_ms, bool force);

    Limits   lim_;
    bool     st_[DEVICE_COUNT];
    uint32_t toggles_[DEVICE_COUNT];
    uint32_t last_change_ms_[DEVICE_COUNT];
    bool     changed_once_[DEVICE_COUNT];
    bool     auto_, remote_active_;
    uint32_t last_cmd_ms_;
    bool     have_cmd_;
    uint32_t ph_cool_until_ms_, ph_pulse_until_ms_;
};

}  // namespace saos
#endif
