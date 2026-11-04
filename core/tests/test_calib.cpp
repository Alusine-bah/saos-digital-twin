#include <cstdio>
#include <cmath>
#include <cstring>
#include "saos_calib.h"
using namespace saos::calib;

static int failures = 0, checks = 0;
#define CHECK(c) do { ++checks; if (!(c)) { ++failures; std::printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)
static bool near(double a, double b, double tol) { return std::fabs(a - b) <= tol; }

int main() {
    // The project's own buffer data (pH 4.01 at 2.925 V, pH 6.86 at 2.314 V)
    PhCalibrator c; c.add(2.925, 4.01, 25); c.add(2.314, 6.86, 25);
    PhCal cal; CHECK(c.fit(cal) == CAL_OK);
    CHECK(near(1.0 / cal.slope_v_per_ph, -4.6639, 0.001));                 // -4.664 pH per volt
    CHECK(near(phFromVoltage(cal, 2.925, 25), 4.01, 1e-9));
    CHECK(near(phFromVoltage(cal, 2.314, 25), 6.86, 1e-9));
    // v1 tutorial constants applied to the same voltages are far off (the problem found in the audit)
    CHECK(near(-5.70 * 2.925 + 21.34, 4.67, 0.01) && near(-5.70 * 2.314 + 21.34, 8.15, 0.01));

    // three-point fit with realistic noise
    PhCalibrator c3; c3.add(2.930, 4.01, 24); c3.add(2.312, 6.86, 25); c3.add(1.790, 9.18, 25);
    PhCal cal3; CHECK(c3.fit(cal3) == CAL_OK && cal3.rms_ph < 0.1 && cal3.n == 3);

    // temperature compensation: a probe in warmer water has a steeper slope, so same voltage offset reads more extreme
    const double v = cal.v7 + cal.slope_v_per_ph * (5.0 - 7.0);
    CHECK(near(phFromVoltage(cal, v, 25), 5.0, 1e-9));
    CHECK(phFromVoltage(cal, v, 35) > 5.0 && phFromVoltage(cal, v, 15) < 5.0);   // 10 C shift moves the reading by about 0.07 pH
    CHECK(near(phFromVoltage(cal, v, 35) - 5.0, 2.0 * (1.0 - 298.15 / 308.15), 0.001));

    // rejection cases
    PhCalibrator one; one.add(2.5, 7.0, 25); CHECK(one.fit(cal) == CAL_TOO_FEW_POINTS);
    PhCalibrator close; close.add(2.5, 6.86, 25); close.add(2.45, 7.5, 25); CHECK(close.fit(cal) == CAL_SPREAD_TOO_SMALL);
    PhCalibrator flat; flat.add(2.50, 4.0, 25); flat.add(2.51, 9.0, 25); CHECK(flat.fit(cal) == CAL_SLOPE_RANGE);
    PhCalibrator hot; hot.add(2.925, 4.01, 10); hot.add(2.314, 6.86, 30); CHECK(hot.fit(cal) == CAL_TEMP_SPREAD);
    PhCalibrator bad; bad.add(2.9, 4.01, 25); bad.add(2.3, 6.86, 25); bad.add(2.6, 9.18, 25); CHECK(bad.fit(cal) == CAL_RESIDUAL_HIGH);
    PhCalibrator full; for (int i = 0; i < 6; ++i) CHECK(full.add(2.5, 7.0 + i, 25)); CHECK(!full.add(2.5, 7.0, 25));

    // drift check
    PhCal a, b; PhCalibrator ca, cb;
    ca.add(2.925, 4.01, 25); ca.add(2.314, 6.86, 25); ca.fit(a);
    cb.add(2.915, 4.01, 25); cb.add(2.306, 6.86, 25); cb.fit(b);
    CHECK(driftOk(a, b, 0.10, 0.20));
    PhCalibrator cc; cc.add(2.80, 4.01, 25); cc.add(2.314, 6.86, 25); PhCal d; cc.fit(d);
    CHECK(!driftOk(a, d, 0.10, 0.20));

    // EEPROM blob: round trip and corruption detection
    uint8_t blob[CAL_BLOB_BYTES]; serialize(cal3, blob); PhCal r;
    CHECK(deserialize(blob, r) && near(r.slope_v_per_ph, cal3.slope_v_per_ph, 1e-5) && r.n == 3 && r.status == CAL_OK);
    for (size_t i = 0; i < CAL_BLOB_BYTES * 8; ++i) { uint8_t w[CAL_BLOB_BYTES]; std::memcpy(w, blob, sizeof w); w[i / 8] ^= (uint8_t)(1u << (i % 8)); PhCal t; CHECK(!deserialize(w, t)); }

    std::printf("%d checks, %d failures\n", checks, failures);
    return failures ? 1 : 0;
}
