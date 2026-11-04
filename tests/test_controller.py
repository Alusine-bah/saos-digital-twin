import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from saos_sim.config import Params
from saos_sim.controller import MegaController
from saos_sim.link import serialization_ms

S = dict(air_c=25, ph=7.0, tds=650, level=50, lux=10000)

def test_fan_hysteresis():
    c = MegaController(Params())
    c.tick(0, {**S, "air_c": 31}, 12); assert c.st["fan"]
    c.tick(1, {**S, "air_c": 29}, 12); assert c.st["fan"]      # inside 28-30 band: stays on
    c.tick(2, {**S, "air_c": 28}, 12); assert not c.st["fan"]

def test_ph_mutually_exclusive_and_fault_guard():
    c = MegaController(Params())
    c.tick(0, {**S, "ph": 6.3}, 12); assert c.st["ph_up"] and not c.st["ph_down"]
    c.tick(1, {**S, "ph": 7.6}, 12); assert c.st["ph_down"] and not c.st["ph_up"]
    c.tick(2, {**S, "ph": 0.0}, 12); assert not c.st["ph_up"] and not c.st["ph_down"]  # probe fault

def test_tank_pump_40_70():
    c = MegaController(Params())
    c.tick(0, {**S, "level": 40}, 12); assert c.st["tank_pump"]
    c.tick(1, {**S, "level": 55}, 12); assert c.st["tank_pump"]
    c.tick(2, {**S, "level": 70}, 12); assert not c.st["tank_pump"]

def test_esp_override_and_8s_watchdog():
    c = MegaController(Params())
    c.esp_command(0, "fan", True)
    c.tick(5, {**S, "air_c": 20}, 12); assert c.st["fan"] and not c.auto      # AUTO suspended
    c.tick(9, {**S, "air_c": 20}, 12); assert c.auto and not c.st["fan"]      # watchdog -> AUTO

def test_uart_serialization():
    assert abs(serialization_ms(100, 115200) - 8.68) < 0.01

def test_no_auto_grow_light():
    c = MegaController(Params())
    c.tick(0, {**S, "lux": 0}, 12); assert not c.st["light"]   # firmware has no light automation

def test_tds_narrow_hysteresis():
    c = MegaController(Params())
    c.tick(0, {**S, "tds": 599}, 12); assert c.st["nutrient"]
    c.tick(1, {**S, "tds": 610}, 12); assert c.st["nutrient"]
    c.tick(2, {**S, "tds": 620}, 12); assert not c.st["nutrient"]
