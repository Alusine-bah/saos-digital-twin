"""Physical plant: greenhouse air, water, tank chemistry, solar/battery."""
import math
import random
from .config import Params


def sun_fraction(hour: float) -> float:
    """0..1 clear-sky irradiance shape, 06:00-18:00 half-sine."""
    if hour < 6 or hour > 18:
        return 0.0
    return math.sin(math.pi * (hour - 6) / 12.0)


class Plant:
    def __init__(self, p: Params):
        self.p = p
        self.rng = random.Random(p.seed)
        self.t = 0.0
        self.air_c = p.amb_mean_c
        self.water_c = p.amb_mean_c - 2.0
        self.alk = p.alk_ref_mgl * 10 ** (7.1 - p.ph_ref)   # mg/L as CaCO3
        self.ph = p.ph_ref + math.log10(self.alk / p.alk_ref_mgl)
        self._alk_pending = 0.0         # dosed but not yet mixed (mg/L)
        self.tds = 650.0
        self.level = 65.0   # firmware default tankLevel = 65
        self.soc_wh = p.battery_wh_usable * 0.8
        self.energy_used_wh = 0.0
        self.energy_in_wh = 0.0
        self.sun = 0.0
        self.amb_c = p.amb_mean_c
        self.lux = 0.0

    def hour(self) -> float:
        return (self.t / 3600.0) % 24.0

    def step(self, act: dict):
        p, dt = self.p, self.p.dt
        h = self.hour()
        # slow cloud/ambient variation (deterministic per seed)
        cloud = p.cloud_factor * (1.0 - 0.25 * (0.5 + 0.5 * math.sin(self.t / 5400.0)))
        self.sun = sun_fraction(h) * cloud
        self.amb_c = (p.amb_mean_c + p.heatwave_c
                      + p.amb_swing_c * math.sin(2 * math.pi * (h - 9) / 24.0))
        self.lux = self.sun * 45000.0 + (1500.0 if act["light"] else 0.0)

        # air temperature
        # exhaust fan vents a fraction of the solar excess and speeds relaxation
        gain = p.solar_gain_c * (1.0 - (p.fan_vent_fraction if act["fan"] else 0.0))
        target = self.amb_c + gain
        tau = p.tau_air_s * ((1.0 - p.fan_vent_fraction) if act["fan"] else 1.0)   # fan raises total conductance by 1/(1-f)
        self.air_c += (target - self.air_c) * dt / tau
        self.water_c += (self.air_c - 2.0 - self.water_c) * dt / p.tau_water_s

        # pH via alkalinity: optional shock, nitrification loss, delayed dosing
        if p.ph_shock_h >= 0 and abs(self.t - p.ph_shock_h * 3600.0) < dt / 2:
            self.alk *= 10 ** p.ph_shock_delta
        dose = 0.0
        if act["ph_up"]:
            dose += p.alk_dose_mgl_per_s * dt
        if act["ph_down"]:
            dose -= p.alk_dose_mgl_per_s * dt
        self._alk_pending += dose
        mixed = self._alk_pending * dt / p.ph_mix_tau_s
        self._alk_pending -= mixed
        self.alk = max(1.0, self.alk + mixed - p.alk_loss_mgl_day * dt / 86400.0)
        self.ph = p.ph_ref + math.log10(self.alk / p.alk_ref_mgl)

        # TDS
        evap = p.level_loss_per_h * dt / 3600.0
        self.tds += (p.tds_rise_per_h - p.tds_uptake_per_h) * dt / 3600.0
        self.tds += self.tds * (evap / max(self.level, 1.0)) * 0.3   # concentration by evaporation
        if act["nutrient"]:
            self.tds += p.tds_dose_per_s * dt

        # level
        self.level -= evap
        if act["tank_pump"]:
            self.level = min(100.0, self.level + p.level_refill_per_s * dt)

        # power
        load = p.p_base_w
        load += p.p_fan_w * act["fan"] + p.p_light_w * act["light"]
        load += p.p_tank_pump_w * act["tank_pump"] + p.p_nutrient_pump_w * act["nutrient"]
        load += p.p_ph_pump_w * (act["ph_up"] or act["ph_down"])
        load += p.p_relay_coil_w * sum(1 for v in act.values() if v)
        gen = p.panel_w * (p.peak_sun_hours / 6.37) * self.sun * p.charge_eff  # 6.37 = integral of half-sine over 12 h / peak
        self.soc_wh += (gen - load) * dt / 3600.0
        self.energy_used_wh += load * dt / 3600.0
        self.energy_in_wh += gen * dt / 3600.0
        self.soc_wh = max(0.0, min(p.battery_wh_usable, self.soc_wh))
        self.load_w, self.gen_w = load, gen
        self.t += dt


class Sensors:
    """What the Mega firmware actually sees, including its filters and cadences.

    DHT11: integer value, one transaction every 2 s (DHTSensor.cpp)
    pH   : trimmed mean + IIR alpha 0.20, updated every 1 s (PHSensor.cpp)
    TDS  : IIR alpha 0.15, two updates per second (TDSSensor.cpp)
    Level: SR04, IIR alpha 0.30, updated every 3 s, stored as integer % (WaterLevelSensor.cpp)
    """

    def __init__(self, plant: Plant, seed: int = 7):
        self.pl = plant
        self.rng = random.Random(seed)
        p = plant.p
        self.dht = round(plant.air_c)
        self._t_dht = -1e9
        self.ph_f = plant.p.ph_cal_gain * plant.ph + plant.p.ph_cal_offset
        self.tds_f = plant.tds
        self.level_f = plant.level
        self.level = round(plant.level)
        self._t_lvl = -1e9

    def read(self) -> dict:
        pl, p, g, t = self.pl, self.pl.p, self.rng.gauss, self.pl.t
        if t - self._t_dht >= 2.0:
            self._t_dht = t
            self.dht = float(round(pl.air_c + p.dht_bias_c + g(0, 0.3)))
        self.ph_f += (p.ph_cal_gain * pl.ph + p.ph_cal_offset + g(0, p.ph_noise) - self.ph_f) * 0.20
        for _ in range(2):
            self.tds_f += (pl.tds + p.tds_bias_ppm + g(0, p.tds_noise) - self.tds_f) * 0.15
        level_new = False
        if t - self._t_lvl >= 3.0:
            self._t_lvl = t
            self.level_f += (pl.level + g(0, p.level_noise) - self.level_f) * 0.30
            self.level = round(self.level_f)
            level_new = True
        return {
            "air_c": self.dht,
            "water_c": pl.water_c + g(0, 0.08),
            "ph": self.ph_f,
            "tds": self.tds_f,
            "level": float(self.level),
            "level_new": level_new,
            "lux": max(0.0, pl.lux + g(0, 150)),
            "pressure": 1008.5,           # [FIRMWARE] hard-coded in Globals.h
            "do_mgl": 0.0,                # [FIRMWARE] never measured
            "soc_pct": 100.0 * pl.soc_wh / p.battery_wh_usable,
        }
