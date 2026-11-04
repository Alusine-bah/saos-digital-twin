import os, sys, struct
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import serial_logger as L


def test_vectors_match_cpp_tests():
    assert L.crc16(b"123456789") == 0x29B1
    assert L.cobs_encode(b"\x00") == b"\x01\x01"
    assert L.cobs_encode(b"\x11\x22\x00\x33") == b"\x03\x11\x22\x02\x33"
    assert L.cobs_decode(b"\x05\x01") is None


def telemetry_payload(**kw):
    d = dict(t=123456, air=2987, water=-50, ph=702, tds=611, level=553, lux=0, mv=12840, ma=-125, sw=0, relays=5, mode=1, valid=0x3F)
    d.update(kw)
    return struct.pack("<IhhHHHHHhHBBB", d["t"], d["air"], d["water"], d["ph"], d["tds"], d["level"], d["lux"], d["mv"], d["ma"], d["sw"], d["relays"], d["mode"], d["valid"])


def test_frame_roundtrip_size_and_gaps():
    p = telemetry_payload()
    assert len(p) == 25
    wire = L.encode(1, 7, p)
    assert len(wire) == 32 and wire[-1] == 0 and 0 not in wire[:-1]           # same 32-byte frame as the C++ test
    d, s = L.Decoder(), L.Stats()
    stream = b"".join(L.encode(1, q, p) for q in (7, 8, 11, 12)) + b"\x13\x77"   # 9, 10 lost
    got = [seq for _, seq, _ in d.feed(stream)]
    for q in got:
        s.add(q)
    assert got == [7, 8, 11, 12] and s.lost == 2 and abs(s.pdr - 66.67) < 0.1
    assert L.telemetry(p)["ph"] == 7.02


def test_corruption_is_rejected_and_resyncs():
    p = telemetry_payload()
    w = bytearray(L.encode(1, 1, p)); w[10] ^= 0x04
    d = L.Decoder()
    assert list(d.feed(bytes(w) + L.encode(1, 2, p))) and d.crc_fail + d.cobs_fail >= 1 and d.good == 1


def test_python_frame_is_byte_identical_to_cpp():
    import subprocess
    core = os.path.join(os.path.dirname(__file__), "..", "core")
    subprocess.run(["make", "-s", "-C", core, "all"], check=True)
    cpp = subprocess.run([os.path.join(core, "build", "dumpframe")], check=True, capture_output=True, text=True).stdout.strip()
    py = L.encode(1, 4242, telemetry_payload(lux=0, sw=0)).hex()
    assert cpp == py
