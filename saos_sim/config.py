"""SAOS simulator parameters.

Every value carries a provenance tag:
  [THESIS]   stated in the thesis
  [FIRMWARE] read from the recovered firmware source
  [ASSUMED]  not recoverable (Config.h and sensor code were lost) - calibrate
             against new hardware before quoting as a measurement.
"""
from dataclasses import dataclass, field


@dataclass
class Params:
    # ---- simulation ------------------------------------------------------
    dt: float = 1.0                     # s, matches Mega scheduler1000ms [FIRMWARE]
    days: float = 2.0
    seed: int = 1

    # ---- control limits --------------------------------------------------
    fan_on_c: float = 30.0              # [FIRMWARE] Config.h EXHAUST_ON_TEMP (DHT11 air temp)
    fan_off_c: float = 28.0             # [FIRMWARE] EXHAUST_OFF_TEMP
    ph_low: float = 6.5                 # [FIRMWARE] PH_LOW_LIMIT (thesis states 6.8)
    ph_high: float = 7.2                # [FIRMWARE] PH_HIGH_LIMIT (thesis states 7.4)
    ph_ctrl_min: float = 2.0            # [FIRMWARE] PH_CONTROL_MIN
    ph_ctrl_max: float = 12.0           # [FIRMWARE] PH_CONTROL_MAX
    tds_low: float = 600.0              # [FIRMWARE] TDS_LOW_LIMIT
    tds_high: float = 620.0             # [FIRMWARE] TDS_HIGH_LIMIT (only 20 ppm hysteresis)
    level_low: float = 40.0             # [FIRMWARE] WaterLevelSensor.cpp pump ON <= 40 % (thesis states 30)
    level_high: float = 70.0            # [FIRMWARE] pump OFF >= 70 % (thesis states 40)
    light_auto: bool = False            # [FIRMWARE] Mega has NO automatic grow-light control
    light_on_lux: float = 300.0         # unused unless light_auto
    light_off_lux: float = 500.0        # [ASSUMED]
    photoperiod: tuple = (6, 18)        # [ASSUMED] grow light allowed 06:00-18:00
    min_on_s: float = 0.0               # [DESIGN] anti short-cycle dwell, 0 = v1 behaviour (same semantics as core Limits::min_on_ms)
    min_off_s: float = 0.0
    esp_timeout_s: float = 8.0          # [FIRMWARE] ESP_REMOTE_TIMEOUT_MS

    # ---- dosing strategy -------------------------------------------------
    ph_strategy: str = "continuous"     # "continuous" = firmware; "pulse" = proposed
    ph_pulse_s: float = 3.0
    ph_wait_s: float = 90.0

    dht_bias_c: float = 0.0             # DHT11 accuracy is +/-2 C; scenario knob
    ph_cal_gain: float = 1.0            # scenario knob: firmware reading = gain*true + offset
    ph_cal_offset: float = 0.0
    ph_noise: float = 0.04              # [ASSUMED] probe+ADC noise after 12-sample trim
    tds_bias_ppm: float = 0.0           # scenario knob: sensor reads true + bias (DFRobot SEN0244 accuracy is +/-10 % of full scale = +/-100 ppm on 0-1000 ppm)
    tds_noise: float = 12.0             # [ASSUMED]
    level_noise: float = 0.8            # [ASSUMED] SR04 jitter in % (tank is only 12 cm tall)

    # ---- plant (all [ASSUMED]; typical aquaponics ranges) ----------------
    # Air node (heat balance): rise above ambient at steady state = q_solar / (UA + rho*cp*Q_fan*fan_on)
    tau_air_s: float = 900.0            # [ASSUMED] air/enclosure time constant; a 217 m2 greenhouse measured 0.75 h and Albright et al. 1985 report ~40 min for dry greenhouses [CITED, via Janius & Jenkins 2004]; a small enclosure should be shorter
    solar_gain_c: float = 12.0          # [DERIVED] rise at full sun without fan: 0.7 x 800 W/m2 / (U 8.82 W/m2K x surface/volume 1.7 x 3 m height) = 12.4 K for a 3 m greenhouse; a rack or enclosure differs, measure it
    fan_vent_fraction: float = 0.60     # [DERIVED] share of the solar rise removed by the fan: 0.57-0.67 for 1.0-1.5 air changes/min (SRAC 5008), 0.70-0.78 at U = 5; see fan_vent_fraction_from_ach()
    tau_water_s: float = 6 * 3600.0     # [ASSUMED] water thermal time constant, about 35 L with weak coupling to the air
    # pH is modelled through alkalinity: at constant dissolved CO2, pH = pH_ref + log10(Alk / Alk_ref)
    # (carbonate system, Henderson-Hasselbalch). Nitrification consumes alkalinity; dosing adds or removes it.
    alk_ref_mgl: float = 100.0          # [CITED] UVI system alkalinity 65-207, means 89-116 mg/L as CaCO3 (Rakocy et al. 2004)
    ph_ref: float = 7.1                 # pH at alk_ref (start value)
    alk_loss_mgl_day: float = 2.9       # NET alkalinity loss. [ESTIMATE] central value for the prototype (see PROTOTYPE_ESTIMATE); UVI net 2.2 [DERIVED], UVI gross 33-41 [DERIVED]
    alk_dose_mgl_per_s: float = 1.4     # [ASSUMED] alkalinity change per second of pH pump; depends on pump flow x reagent strength x tank volume
    ph_mix_tau_s: float = 120.0         # mixing lag between dosing and probe
    tds_rise_per_h: float = 6.0         # ppm/h fish waste + feed
    tds_uptake_per_h: float = 11.0      # ppm/h plant uptake
    tds_dose_per_s: float = 2.5         # ppm per second of nutrient pump
    level_loss_per_h: float = 0.17      # [DERIVED] % of the 12 cm level scale per hour: about 5 mm/day (3.7 mm/day pan evaporation, equatorial Central Africa, Riou 1984, plus ~1 mm/day lettuce use) / 1.2 mm per %. Was 0.9 [ASSUMED], about 5x too high. Check: 5 mm of a 14-29 L tank = 0.6-1.2 L/day = 1.7-3.4 % of a 35 L system vs UVI make-up 2.4 % and 1-1.5 % in extension guidance
    level_refill_per_s: float = 0.04    # % per second tank pump on
    tank_volume_l: float = 100.0

    ph_shock_h: float = -1.0            # scenario knob: time of acid/base shock (h), -1 = none
    ph_shock_delta: float = 0.0

    # ---- power -----------------------------------------------------------
    p_base_w: float = 4.2               # [ASSUMED, thesis-era] Mega + ESP32 + sensors + LCD. Component sum is closer to 2.2 W [DERIVED, see docs/LITERATURE.md topic 5]; kept at 4.2 until the real prototype load is measured
    p_relay_coil_w: float = 0.36        # [CITED] 5 V SRD-05VDC-SL-C relay coil 360 mW (71.4 mA) per relay that is ON
    p_fan_w: float = 2.5
    p_light_w: float = 6.0
    p_tank_pump_w: float = 4.5
    p_ph_pump_w: float = 2.2            # [ASSUMED] a common 12 V peristaltic dosing pump is rated 5 W (0.4 A) [CITED, one product class]; prototype pump unknown
    p_nutrient_pump_w: float = 2.2
    panel_w: float = 100.0              # [THESIS]
    battery_wh_usable: float = 120.0    # [THESIS] 12 V / 20 Ah at 50 % DoD
    charge_eff: float = 0.85            # [ASSUMED]
    peak_sun_hours: float = 5.0         # [THESIS]
    cloud_factor: float = 1.0           # scenario knob

    # ---- ambient ---------------------------------------------------------
    amb_mean_c: float = 29.0            # [ASSUMED] Sub-Saharan / Bangladesh-like
    amb_swing_c: float = 5.0
    heatwave_c: float = 0.0             # scenario knob (added to ambient)

    # ---- link ------------------------------------------------------------
    baud: int = 9600                    # [FIRMWARE] Serial2.begin(9600) in SAOS_Mega_V_9_0_0.ino (thesis says 115200)
    frame_period_s: float = 1.0         # [FIRMWARE] sensorTimer 1000 ms (thesis measured ~0.55 frames/s)
    frame_loss: float = 0.0             # scenario knob (thesis run: 0.07)
    packet_buffer: int = 384            # [FIRMWARE] SPSAS_PACKET_SIZE
    mega_loop_ms: tuple = (4.0, 40.0)   # [ASSUMED] range of loop time with LCD I2C
    esp_http_ms: tuple = (6.0, 18.0)    # [ASSUMED] ESP32 handler + queue time


def alk_loss_from_feed(feed_g_per_day: float, volume_l: float, tan_per_feed: float = 0.03,
                       alk_per_tan: float = 7.14, plant_offset: float = 0.0) -> float:
    """Alkalinity loss (mg/L as CaCO3 per day) from feeding.

    tan_per_feed  : kg TAN produced per kg feed, about 0.03 (Ebeling, RAS short course rule of thumb; a table in the
                    same document implies about 0.05 for 35 % protein feed)
    alk_per_tan   : 7.14 g alkalinity per g TAN nitrified (Ebeling), 7.05 from overall stoichiometry
    plant_offset  : fraction (0..1) of the gross loss offset by plant nitrate uptake and denitrification.
                    The UVI system's base use implies a net loss of 5-7 % of gross (offset 0.93-0.95) when
                    0.03 kg TAN/kg feed is used (3 % if 0.05); see docs/LITERATURE.md for the derivation.
    """
    gross_g = feed_g_per_day * tan_per_feed * alk_per_tan          # g CaCO3 per day
    return gross_g * 1000.0 / volume_l * (1.0 - plant_offset)       # mg/L per day


# Prototype estimate. The thesis gives no tank volume, fish number or feed. These are ESTIMATES made from
# the firmware geometry (TANK_HEIGHT = 12 cm water column) and published practice; replace with measurements.
PROTOTYPE_ESTIMATE = dict(
    fish_tank_l=(14.4, 28.8),          # 12 cm x (40x30 cm .. 60x40 cm) shelf footprint [ESTIMATE]
    system_volume_l=(20.0, 50.0),      # tank + grow-bed reservoir + pipes, central 35 L [ESTIMATE]
    feed_g_per_day=(4.0, 12.0),        # central 8 g; 0.15-0.45 kg of juvenile tilapia at about 3 % body weight/day [ESTIMATE, rule of thumb]
    plant_offset=0.94,                 # from the UVI net/gross ratio [DERIVED]
)


RHO_AIR, CP_AIR = 1.2, 1005.0          # kg/m3, J/(kg K)


def fan_vent_fraction_from_ach(ach_per_min: float, u_w_m2k: float = 8.82, surface_to_volume: float = 1.7) -> float:
    """Share of the no-fan solar temperature rise removed by a fan moving `ach_per_min` air volumes per minute.

    Steady-state heat balance: rise = q / (UA + rho*cp*Q)  ->  removed share = rho*cp*Q / (UA + rho*cp*Q).
    U = 5 + 1.2 v (v = 3.18 m/s gives 8.82 W/m2K) from Janius & Jenkins (2004); 1.0-1.5 air changes per minute from
    Pickens & Danaher (2016) SRAC 5008 and Watson et al. (2019) UF/IFAS AE-10. Surface/volume 1.7 assumes a 3 m high house.
    """
    q = RHO_AIR * CP_AIR * ach_per_min / 60.0       # W/K per m3
    ua = u_w_m2k * surface_to_volume                 # W/K per m3
    return q / (q + ua)
