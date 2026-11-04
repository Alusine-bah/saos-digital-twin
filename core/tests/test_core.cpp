#include <cstdio>
#include <cmath>
#include "saos_core.h"
using namespace saos;

static int failures = 0, checks = 0;
#define CHECK(c) do { ++checks; if (!(c)) { ++failures; std::printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

static Inputs base() { Inputs i; i.air_c = 25; i.ph = 7.0; i.tds = 610; i.level = 55; i.level_new = true; i.hour = 12; i.lux = 10000; return i; }

static void fan_hysteresis() {
    Limits l; Controller c(l); Inputs i = base();
    i.air_c = 31; c.tick(0, i);    CHECK(c.get(FAN));
    i.air_c = 29; c.tick(1000, i); CHECK(c.get(FAN));
    i.air_c = 28; c.tick(2000, i); CHECK(!c.get(FAN));
}
static void fan_min_dwell() {                       // v2 anti short-cycle
    Limits l; l.min_on_ms = 60000; l.min_off_ms = 60000; Controller c(l); Inputs i = base();
    i.air_c = 31; c.tick(0, i);        CHECK(c.get(FAN));
    i.air_c = 27; c.tick(10000, i);    CHECK(c.get(FAN));      // too soon to stop
    c.tick(61000, i);                  CHECK(!c.get(FAN));
    i.air_c = 31; c.tick(70000, i);    CHECK(!c.get(FAN));     // too soon to restart
    c.tick(122000, i);                 CHECK(c.get(FAN));
    CHECK(c.toggles(FAN) == 3);
}
static void ph_exclusion_and_fault() {
    Limits l; Controller c(l); Inputs i = base();
    i.ph = 6.0; c.tick(0, i);     CHECK(c.get(PH_UP) && !c.get(PH_DOWN));
    i.ph = 8.0; c.tick(1000, i);  CHECK(c.get(PH_DOWN) && !c.get(PH_UP));
    i.ph = 0.0; c.tick(2000, i);  CHECK(!c.get(PH_UP) && !c.get(PH_DOWN));       // probe fault
    i.ph = NAN; c.tick(3000, i);  CHECK(!c.get(PH_UP) && !c.get(PH_DOWN));
}
static void ph_pulse_mode() {
    Limits l; l.ph_mode = PH_PULSE; Controller c(l); Inputs i = base(); i.ph = 6.0;
    c.tick(0, i);      CHECK(c.get(PH_UP));
    c.tick(2000, i);   CHECK(c.get(PH_UP));        // inside 3 s pulse
    c.tick(3000, i);   CHECK(!c.get(PH_UP));       // pulse over, waiting
    c.tick(60000, i);  CHECK(!c.get(PH_UP));
    c.tick(94000, i);  CHECK(c.get(PH_UP));        // wait (90 s after pulse) finished
}
static void tds_and_tank() {
    Limits l; Controller c(l); Inputs i = base();
    i.tds = 599; c.tick(0, i);      CHECK(c.get(NUTRIENT));
    i.tds = 610; c.tick(1000, i);   CHECK(c.get(NUTRIENT));
    i.tds = 620; c.tick(2000, i);   CHECK(!c.get(NUTRIENT));
    i.level = 40; c.tick(3000, i);  CHECK(c.get(TANK_PUMP));
    i.level = 55; c.tick(4000, i);  CHECK(c.get(TANK_PUMP));
    i.level_new = false; i.level = 80; c.tick(5000, i); CHECK(c.get(TANK_PUMP));  // no fresh sample
    i.level_new = true;  c.tick(6000, i);               CHECK(!c.get(TANK_PUMP));
    i.level = NAN; i.level_new = true; c.tick(7000, i); CHECK(!c.get(TANK_PUMP));
}
static void esp_override_and_watchdog() {
    Limits l; Controller c(l); Inputs i = base(); i.air_c = 20;
    c.espCommand(0, FAN, true);
    c.tick(5000, i);   CHECK(c.get(FAN) && !c.autoActive());
    c.tick(8000, i);   CHECK(c.get(FAN) && !c.autoActive());     // exactly 8 s: still owned
    c.tick(9000, i);   CHECK(c.autoActive() && !c.get(FAN));     // > 8 s: back to AUTO
    c.espCommand(10000, PH_UP, true); c.espCommand(10100, PH_DOWN, true);
    CHECK(c.get(PH_DOWN) && !c.get(PH_UP));                      // doser exclusion also for ESP commands
}
static void light_schedule() {
    Limits l; l.light_auto = true; Controller c(l); Inputs i = base();
    i.hour = 5; i.lux = 0; c.tick(0, i);        CHECK(!c.get(LIGHT));
    i.hour = 7; c.tick(1000, i);                CHECK(c.get(LIGHT));
    i.lux = 800; c.tick(2000, i);               CHECK(!c.get(LIGHT));
    i.hour = 19; i.lux = 0; c.tick(3000, i);    CHECK(!c.get(LIGHT));
    Limits v1; Controller d(v1); Inputs j = base(); j.hour = 7; j.lux = 0; d.tick(0, j);
    CHECK(!d.get(LIGHT));                                        // v1 default: no automatic light
}
static void sensor_loss_is_safe() {
    Limits l; Controller c(l); Inputs i = base();
    i.air_c = 31; c.tick(0, i); CHECK(c.get(FAN));
    i.air_c = NAN; c.tick(1000, i); CHECK(!c.get(FAN));
}

int main() {
    fan_hysteresis(); fan_min_dwell(); ph_exclusion_and_fault(); ph_pulse_mode();
    tds_and_tank(); esp_override_and_watchdog(); light_schedule(); sensor_loss_is_safe();
    std::printf("%d checks, %d failures\n", checks, failures);
    return failures ? 1 : 0;
}
