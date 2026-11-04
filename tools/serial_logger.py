"""Decode SAOS v2 frames from a serial port (or a captured file) and report delivery ratio, gaps and CRC errors.
usage: python tools/serial_logger.py COM5 9600 [seconds]      (needs: pip install pyserial)
       python tools/serial_logger.py capture.bin              (raw bytes saved earlier)
Wire format must match core/src/saos_proto.cpp: COBS( type | seq16 | payload | crc16 ) 0x00, CRC-16/CCITT-FALSE."""
import struct, sys, time


def crc16(data: bytes) -> int:
    c = 0xFFFF
    for b in data:
        c ^= b << 8
        for _ in range(8):
            c = ((c << 1) ^ 0x1021) & 0xFFFF if c & 0x8000 else (c << 1) & 0xFFFF
    return c


def cobs_encode(data: bytes) -> bytes:
    out, idx, code = bytearray([0]), 0, 1
    for b in data:
        if b == 0:
            out[idx] = code; idx = len(out); out.append(0); code = 1
        else:
            out.append(b); code += 1
            if code == 0xFF:
                out[idx] = code; idx = len(out); out.append(0); code = 1
    out[idx] = code
    return bytes(out)


def cobs_decode(data: bytes):
    out, i = bytearray(), 0
    while i < len(data):
        code = data[i]
        if code == 0 or i + code > len(data):
            return None
        out += data[i + 1:i + code]
        i += code
        if code < 0xFF and i < len(data):
            out.append(0)
    return bytes(out)


def encode(msg_type: int, seq: int, payload: bytes) -> bytes:
    raw = bytes([msg_type]) + struct.pack("<H", seq) + payload
    raw += struct.pack("<H", crc16(raw))
    return cobs_encode(raw) + b"\x00"


class Decoder:
    def __init__(self):
        self.buf = bytearray(); self.good = self.crc_fail = self.cobs_fail = self.too_short = 0

    def feed(self, data: bytes):
        """Yield (type, seq, payload) for every valid frame in `data`."""
        for b in data:
            if b != 0:
                self.buf.append(b); continue
            frame, self.buf = bytes(self.buf), bytearray()
            if not frame:
                continue
            raw = cobs_decode(frame)
            if raw is None:
                self.cobs_fail += 1; continue
            if len(raw) < 5:
                self.too_short += 1; continue
            if crc16(raw[:-2]) != struct.unpack("<H", raw[-2:])[0]:
                self.crc_fail += 1; continue
            self.good += 1
            yield raw[0], struct.unpack("<H", raw[1:3])[0], raw[3:-2]


def telemetry(p: bytes):
    t = struct.unpack("<IhhHHHHHhHBBB", p)
    return dict(t_ms=t[0], air_c=t[1] / 100, water_c=t[2] / 100, ph=t[3] / 100, tds=t[4], level=t[5] / 10, lux=t[6],
                batt_v=t[7] / 1000, batt_a=t[8] / 10, solar_w=t[9] / 10, relays=t[10], mode=t[11], valid=t[12])


class Stats:
    def __init__(self):
        self.rx = self.lost = 0; self.last = None

    def add(self, seq):
        if self.last is not None:
            gap = (seq - self.last) & 0xFFFF
            if gap == 0:
                return
            if 1 < gap < 1000:
                self.lost += gap - 1
        self.last = seq; self.rx += 1

    @property
    def pdr(self):
        return 100.0 * self.rx / (self.rx + self.lost) if self.rx + self.lost else 0.0


def main(argv):
    dec, stats = Decoder(), Stats()
    if len(argv) == 2:
        chunks = [open(argv[1], "rb").read()]
    else:
        import serial
        ser = serial.Serial(argv[1], int(argv[2]), timeout=0.2)
        end = time.time() + (float(argv[3]) if len(argv) > 3 else 60.0)
        chunks = iter(lambda: ser.read(256) if time.time() < end else b"", b"")
    for chunk in chunks:
        for typ, seq, payload in dec.feed(chunk):
            if typ == 1:
                stats.add(seq)
                if stats.rx % 10 == 1:
                    print(telemetry(payload))
    print(f"telemetry received {stats.rx}, lost (sequence gaps) {stats.lost}, PDR {stats.pdr:.2f} %, "
          f"CRC errors {dec.crc_fail}, COBS errors {dec.cobs_fail}, short {dec.too_short}")


if __name__ == "__main__":
    main(sys.argv)
