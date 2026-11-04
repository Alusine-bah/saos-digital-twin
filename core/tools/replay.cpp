// Replays an input trace through the C++ controller and prints the outputs.
// usage: replay trace.csv [key=value ...]    keys: pulse=1 light_auto=1 min_on_s=.. min_off_s=..
// trace columns: t_s,hour,air_c,ph,tds,level,level_new,lux
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include "saos_core.h"

int main(int argc, char** argv) {
    if (argc < 2) { std::fprintf(stderr, "usage: replay trace.csv [key=value...]\n"); return 2; }
    saos::Limits lim;
    for (int i = 2; i < argc; ++i) {
        const char* a = argv[i];
        if (!std::strncmp(a, "pulse=", 6))      lim.ph_mode = std::atoi(a + 6) ? saos::PH_PULSE : saos::PH_CONTINUOUS;
        else if (!std::strncmp(a, "light_auto=", 11)) lim.light_auto = std::atoi(a + 11) != 0;
        else if (!std::strncmp(a, "min_on_s=", 9))    lim.min_on_ms = (uint32_t)(std::atof(a + 9) * 1000);
        else if (!std::strncmp(a, "min_off_s=", 10))  lim.min_off_ms = (uint32_t)(std::atof(a + 10) * 1000);
        else { std::fprintf(stderr, "unknown option %s\n", a); return 2; }
    }
    FILE* f = std::fopen(argv[1], "r");
    if (!f) { std::perror("open"); return 2; }
    char line[512];
    saos::Controller ctl(lim);
    std::printf("t_s,fan,ph_up,ph_down,nutrient,light,tank_pump\n");
    if (!std::fgets(line, sizeof line, f)) return 2;              // header
    while (std::fgets(line, sizeof line, f)) {
        double t, hour, air, ph, tds, level, lux; int lnew;
        if (std::sscanf(line, "%lf,%lf,%lf,%lf,%lf,%lf,%d,%lf", &t, &hour, &air, &ph, &tds, &level, &lnew, &lux) != 8) continue;
        saos::Inputs in;
        in.air_c = air; in.ph = ph; in.tds = tds; in.level = level;
        in.level_new = lnew != 0; in.hour = hour; in.lux = lux;
        ctl.tick((uint32_t)(t * 1000.0 + 0.5), in);
        std::printf("%.0f,%d,%d,%d,%d,%d,%d\n", t, ctl.get(saos::FAN), ctl.get(saos::PH_UP), ctl.get(saos::PH_DOWN),
                    ctl.get(saos::NUTRIENT), ctl.get(saos::LIGHT), ctl.get(saos::TANK_PUMP));
    }
    std::fclose(f);
    return 0;
}
