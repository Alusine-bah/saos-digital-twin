// SAOS v2 ESP32 gateway (first hardware-facing draft).
// STATUS: syntax-checked on a PC with stubs only. NOT compiled for the ESP32 toolchain, NOT run on hardware.
// The ESP32 makes no control decisions: it relays operator requests and shows what the Mega reports.
#include <WiFi.h>
#include <WebServer.h>
#include "saos_gateway.h"
#include "wifi_secrets.h"        // copy wifi_secrets.example.h; never commit the real file

using namespace saos;
static const uint32_t LINK_BAUD = 57600;      // must equal the Mega's LINK_BAUD
static const int RX_PIN = 16, TX_PIN = 17;    // v1 wiring: Serial2 on GPIO16/17

gw::Gateway gateway;
WebServer server(80);

static const char PAGE[] PROGMEM =
"<!doctype html><meta name=viewport content='width=device-width,initial-scale=1'><title>SAOS</title>"
"<pre id=o>loading...</pre><script>"
"async function t(){try{const r=await fetch('/json');o.textContent=JSON.stringify(await r.json(),null,1)}catch(e){o.textContent='no link to gateway'}}"
"t();setInterval(t,1000)</script>";

static bool deviceFromName(const String& s, Device& d) {
    static const char* names[DEVICE_COUNT] = {"fan", "ph_up", "ph_down", "nutrient", "light", "tank_pump"};
    for (int i = 0; i < DEVICE_COUNT; ++i) if (s == names[i]) { d = (Device)i; return true; }
    return false;
}
static bool authorised() { return server.arg("key") == API_KEY; }

void setup() {
    Serial2.begin(LINK_BAUD, SERIAL_8N1, RX_PIN, TX_PIN);
    WiFi.mode(WIFI_STA); WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    server.on("/", []() { server.send_P(200, "text/html", PAGE); });
    server.on("/json", []() {
        char buf[420]; size_t n = gateway.snapshotJson(buf, sizeof buf, millis());
        if (n) server.send(200, "application/json", buf); else server.send(500, "text/plain", "buffer");
    });
    server.on("/cmd", []() {                                      // /cmd?dev=fan&val=1&key=...  (hold device ON/OFF)
        Device d; if (!authorised()) { server.send(403, "text/plain", "key"); return; }
        if (!deviceFromName(server.arg("dev"), d)) { server.send(400, "text/plain", "dev"); return; }
        gateway.request(d, server.arg("val") == "1", millis()); server.send(200, "text/plain", "ok");
    });
    server.on("/release", []() {                                  // /release?dev=fan&key=...  (Mega returns to AUTO after its timeout)
        Device d; if (!authorised()) { server.send(403, "text/plain", "key"); return; }
        if (!deviceFromName(server.arg("dev"), d)) { server.send(400, "text/plain", "dev"); return; }
        gateway.release(d); server.send(200, "text/plain", "ok");
    });
    server.begin();
}

void loop() {
    uint32_t now = millis();
    while (Serial2.available()) gateway.onByte((uint8_t)Serial2.read(), now);
    uint8_t w[proto::MAX_WIRE]; size_t n = gateway.poll(now, w, sizeof w); if (n) Serial2.write(w, n);
    server.handleClient();
}
