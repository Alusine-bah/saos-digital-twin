// SAOS v2 pH calibration. Pure C++11, no heap/STL (AVR-safe).
// Model: probe voltage V = v7 + s * (pH - 7), with s in volts per pH (negative for most PH4502C modules).
// Temperature: the electrode slope scales with absolute temperature (Nernst), the isopotential point stays at pH 7.
#ifndef SAOS_CALIB_H
#define SAOS_CALIB_H

#include <stdint.h>
#include <stddef.h>
#include "saos_core.h"      // real_t

namespace saos { namespace calib {

enum Status : uint8_t {
    CAL_OK = 0, CAL_TOO_FEW_POINTS, CAL_SPREAD_TOO_SMALL, CAL_SLOPE_RANGE,
    CAL_RESIDUAL_HIGH, CAL_TEMP_SPREAD, CAL_DEGENERATE
};

// Acceptance limits are DESIGN CHOICES; tune per probe/module after the literature review.
struct Limits {
    real_t min_ph_spread;        // pH units between lowest and highest buffer
    real_t min_abs_slope;        // V/pH
    real_t max_abs_slope;        // V/pH
    real_t max_rms_ph;           // fit residual
    real_t max_temp_spread_c;    // buffers must be measured at similar temperature
    Limits() : min_ph_spread(2.0), min_abs_slope(0.05), max_abs_slope(0.50), max_rms_ph(0.10), max_temp_spread_c(5.0) {}
};

struct PhCal {
    real_t slope_v_per_ph, v7, t_ref_c, rms_ph, max_ph;
    uint8_t n, status;
};

class PhCalibrator {
public:
    PhCalibrator() : n_(0) {}
    void reset() { n_ = 0; }
    bool add(real_t volts, real_t buffer_ph, real_t temp_c);      // false if full (max 6 points)
    uint8_t count() const { return n_; }
    uint8_t fit(PhCal& out, const Limits& lim = Limits()) const;  // returns Status, fills out either way
private:
    real_t v_[6], ph_[6], t_[6];
    uint8_t n_;
};

real_t phFromVoltage(const PhCal& cal, real_t volts, real_t temp_c);

// Compare a new calibration with the stored one (probe aging / reference drift).
bool driftOk(const PhCal& prev, const PhCal& now, real_t max_slope_change_frac, real_t max_v7_shift_ph);

static const size_t CAL_BLOB_BYTES = 20;
void serialize(const PhCal& cal, uint8_t out[CAL_BLOB_BYTES]);   // 4 floats + n + status + CRC-16, little-endian
bool deserialize(const uint8_t in[CAL_BLOB_BYTES], PhCal& cal);  // false if CRC fails

}}  // namespace saos::calib
#endif
