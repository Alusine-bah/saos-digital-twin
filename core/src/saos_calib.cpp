#include "saos_calib.h"
#include "saos_proto.h"      // crc16
#include <math.h>
#include <string.h>

namespace saos { namespace calib {

bool PhCalibrator::add(real_t volts, real_t buffer_ph, real_t temp_c) {
    if (n_ >= 6) return false;
    v_[n_] = volts; ph_[n_] = buffer_ph; t_[n_] = temp_c; ++n_;
    return true;
}

uint8_t PhCalibrator::fit(PhCal& out, const Limits& lim) const {
    out.slope_v_per_ph = 0; out.v7 = 0; out.t_ref_c = 25; out.rms_ph = 0; out.max_ph = 0; out.n = n_;
    if (n_ < 2) return out.status = CAL_TOO_FEW_POINTS;

    real_t pmin = ph_[0], pmax = ph_[0], tmin = t_[0], tmax = t_[0], tsum = 0;
    for (uint8_t i = 0; i < n_; ++i) {
        if (ph_[i] < pmin) pmin = ph_[i];
        if (ph_[i] > pmax) pmax = ph_[i];
        if (t_[i] < tmin) tmin = t_[i];
        if (t_[i] > tmax) tmax = t_[i];
        tsum += t_[i];
    }
    out.t_ref_c = tsum / n_;
    if (pmax - pmin < lim.min_ph_spread) return out.status = CAL_SPREAD_TOO_SMALL;

    // least squares  V = a + s * x,  x = pH - 7
    real_t sx = 0, sy = 0, sxx = 0, sxy = 0;
    for (uint8_t i = 0; i < n_; ++i) {
        const real_t x = ph_[i] - 7.0, y = v_[i];
        sx += x; sy += y; sxx += x * x; sxy += x * y;
    }
    const real_t den = n_ * sxx - sx * sx;
    if (den == 0) return out.status = CAL_DEGENERATE;
    const real_t s = (n_ * sxy - sx * sy) / den;
    const real_t a = (sy - s * sx) / n_;
    out.slope_v_per_ph = s; out.v7 = a;
    if (!(s == s) || fabs(s) < lim.min_abs_slope || fabs(s) > lim.max_abs_slope) return out.status = CAL_SLOPE_RANGE;

    real_t ss = 0, mx = 0;
    for (uint8_t i = 0; i < n_; ++i) {
        const real_t e = (v_[i] - (a + s * (ph_[i] - 7.0))) / s;       // residual in pH units
        ss += e * e; if (fabs(e) > mx) mx = fabs(e);
    }
    out.rms_ph = sqrt(ss / n_); out.max_ph = mx;
    if (tmax - tmin > lim.max_temp_spread_c) return out.status = CAL_TEMP_SPREAD;
    if (n_ > 2 && out.rms_ph > lim.max_rms_ph) return out.status = CAL_RESIDUAL_HIGH;   // 2 points always fit exactly
    return out.status = CAL_OK;
}

real_t phFromVoltage(const PhCal& cal, real_t volts, real_t temp_c) {
    const real_t scale = (temp_c + 273.15) / (cal.t_ref_c + 273.15);    // slope grows with absolute temperature
    return 7.0 + (volts - cal.v7) / (cal.slope_v_per_ph * scale);
}

bool driftOk(const PhCal& prev, const PhCal& now, real_t max_slope_change_frac, real_t max_v7_shift_ph) {
    const real_t ds = fabs(now.slope_v_per_ph - prev.slope_v_per_ph) / fabs(prev.slope_v_per_ph);
    const real_t dv = fabs(now.v7 - prev.v7) / fabs(now.slope_v_per_ph);       // offset shift expressed in pH
    return ds <= max_slope_change_frac && dv <= max_v7_shift_ph;
}

void serialize(const PhCal& c, uint8_t out[CAL_BLOB_BYTES]) {
    const float f[4] = { (float)c.slope_v_per_ph, (float)c.v7, (float)c.t_ref_c, (float)c.rms_ph };
    memcpy(out, f, 16);
    out[16] = c.n; out[17] = c.status;
    const uint16_t crc = proto::crc16(out, 18);
    out[18] = (uint8_t)(crc & 0xFF); out[19] = (uint8_t)(crc >> 8);
}

bool deserialize(const uint8_t in[CAL_BLOB_BYTES], PhCal& c) {
    const uint16_t got = (uint16_t)(in[18] | ((uint16_t)in[19] << 8));
    if (proto::crc16(in, 18) != got) return false;
    float f[4]; memcpy(f, in, 16);
    c.slope_v_per_ph = f[0]; c.v7 = f[1]; c.t_ref_c = f[2]; c.rms_ph = f[3]; c.max_ph = 0;
    c.n = in[16]; c.status = in[17];
    return true;
}

}}  // namespace saos::calib
