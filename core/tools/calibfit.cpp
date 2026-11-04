// usage: calibfit points.csv [query_volts query_temp]      points.csv columns: volts,ph,temp_c (with header)
#include <cstdio>
#include <cstdlib>
#include "saos_calib.h"
using namespace saos::calib;
int main(int argc, char** argv) {
    if (argc < 2) return 2;
    FILE* f = std::fopen(argv[1], "r"); if (!f) return 2;
    char line[256]; PhCalibrator c; if (!std::fgets(line, sizeof line, f)) return 2;
    while (std::fgets(line, sizeof line, f)) { double v, p, t; if (std::sscanf(line, "%lf,%lf,%lf", &v, &p, &t) == 3) c.add(v, p, t); }
    std::fclose(f);
    PhCal cal; const int st = c.fit(cal);
    std::printf("status=%d\nslope=%.12g\nv7=%.12g\nrms=%.12g\nmax=%.12g\n", st, cal.slope_v_per_ph, cal.v7, cal.rms_ph, cal.max_ph);
    if (argc >= 4) std::printf("ph=%.12g\n", phFromVoltage(cal, std::atof(argv[2]), std::atof(argv[3])));
    return 0;
}
