"""Mega 2560 control logic, ported from ActuatorManager.cpp / Scheduler.cpp.

Behaviour kept identical to the firmware as read:
  * decisions run every 1000 ms (scheduler1000ms)
  * pH up / pH down mutually exclusive, dead band, sensor-fault guard
  * TDS and fan are hysteresis loops
  * any ESP32 actuator command -> AUTO suspended; after 8 s of silence -> AUTO
"""
from .config import Params


class MegaController:
    def __init__(self, p: Params):
        self.p = p
        self.st = dict(fan=False, ph_up=False, ph_down=False,
                       nutrient=False, light=False, tank_pump=False)
        self.auto = True
        self.remote_active = False
        self._last_cmd_t = -1e9
        self._ph_cool_until = 0.0
        self._ph_pulse_until = 0.0
        self.toggles = {k: 0 for k in self.st}
        self._last_change = {}
        self._now = 0.0

    # ---- ESP32 interface -------------------------------------------------
    def esp_command(self, t: float, device: str, on: bool):
        self.remote_active = True
        self.auto = False
        self._last_cmd_t = t
        self._set(device, on)

    def _set(self, k, v, force=True):
        """force=True bypasses the dwell timers (ESP32 commands, pH dosers, safety), as in core Controller::set."""
        v = bool(v)
        if self.st[k] == v:
            return
        if not force and k in self._last_change:
            held = self._now - self._last_change[k]
            if self.st[k] and held < self.p.min_on_s:
                return
            if (not self.st[k]) and held < self.p.min_off_s:
                return
        self.toggles[k] += 1
        self.st[k] = v
        self._last_change[k] = self._now

    # ---- 1 Hz control tick ----------------------------------------------
    def tick(self, t: float, s: dict, hour: float):
        p = self.p
        self._now = t
        if self.remote_active and (t - self._last_cmd_t) > p.esp_timeout_s:
            self.remote_active = False
            self.auto = True
        if self.remote_active or not self.auto:
            return dict(self.st)

        # exhaust fan (hysteresis)
        if s["air_c"] >= p.fan_on_c:
            self._set("fan", True, False)
        elif s["air_c"] <= p.fan_off_c:
            self._set("fan", False, False)

        # pH dosing
        ph = s["ph"]
        valid = p.ph_ctrl_min < ph < p.ph_ctrl_max
        if not valid:
            self._set("ph_up", False); self._set("ph_down", False)
        elif p.ph_strategy == "continuous":
            self._set("ph_up", ph < p.ph_low)
            self._set("ph_down", ph > p.ph_high)
        else:  # pulse-and-wait (proposed improvement)
            if t < self._ph_pulse_until:
                pass                                  # keep current pulse
            else:
                self._set("ph_up", False); self._set("ph_down", False)
                if t >= self._ph_cool_until:
                    if ph < p.ph_low:
                        self._set("ph_up", True)
                    elif ph > p.ph_high:
                        self._set("ph_down", True)
                    if self.st["ph_up"] or self.st["ph_down"]:
                        self._ph_pulse_until = t + p.ph_pulse_s
                        self._ph_cool_until = t + p.ph_pulse_s + p.ph_wait_s

        # nutrient / TDS (hysteresis)
        if s["tds"] <= p.tds_low:
            self._set("nutrient", True)
        elif s["tds"] >= p.tds_high:
            self._set("nutrient", False)
        # tank pump: evaluated inside readWaterLevel() every 3 s (WaterLevelSensor.cpp)
        if s.get("level_new", True):
            if s["level"] <= p.level_low:
                self._set("tank_pump", True, False)
            elif s["level"] >= p.level_high:
                self._set("tank_pump", False, False)
        # grow light: the Mega firmware has no automatic light control at all.
        if p.light_auto:
            in_window = p.photoperiod[0] <= hour < p.photoperiod[1]
            if in_window and s["lux"] < p.light_on_lux:
                self._set("light", True, False)
            elif (not in_window) or s["lux"] > p.light_off_lux:
                self._set("light", False, False)
        return dict(self.st)
