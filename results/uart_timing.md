# UART timing for the Mega 2560 <-> ESP32 link

Computed from cited rules (see docs/LITERATURE.md topic 6). 8N1 = 10 bits per byte.

| Baud | Byte time (ms) | 32 B v2 frame (ms) | 205 B v1 frame (ms) | Mega 16 MHz actual baud (U2X) | Baud error | 64 B RX buffer drains in (ms) |
|---|---|---|---|---|---|---|
| 9600 | 1.04 | 33.3 | 213.5 | 9615 | +0.16 % | 66.7 |
| 38400 | 0.26 | 8.3 | 53.4 | 38462 | +0.16 % | 16.7 |
| 57600 | 0.17 | 5.6 | 35.6 | 57143 | -0.79 % | 11.1 |
| 115200 | 0.087 | 2.8 | 17.8 | 117647 | +2.12 % | 5.6 |

Reading the table:
* v1 wrote a 205-byte frame into a 64-byte TX buffer, so `Serial.write` blocked for (205 - 64) x 1.04 ms = 147 ms per frame (matches the link benchmark, 146.9 ms/s). The 32-byte v2 frame fits the buffer and never blocks.
* 115200 on a 16 MHz AVR has +2.12 % baud error, above the 1.5 % receiver error the Microchip tolerance table recommends for double-speed mode (total tolerance is -4.0/+3.9 %, and the ESP32 side is accurate, so it works but with little margin). 38400 (0.16 %) and 57600 (-0.79 %) have more margin. **Recommended v2 rate: 57600** (5.6 ms per telemetry frame; 1 Hz telemetry uses 0.6 % of the link).
* The Mega's receive buffer overflows if the main loop is blocked for longer than the last column AND more than 64 bytes arrive meanwhile. A single 13-byte command cannot do that, but a burst of commands could. The gateway now spaces frames at least 20 ms apart (tested: at most 64 bytes in any 16 ms window with 6 devices held), and the Mega sketch's ultrasonic `pulseIn` timeout was cut from 30 ms to 4 ms.
