#pragma once
#include "Arduino.h"
#include <functional>
struct WebServer { WebServer(int); void on(const char*, std::function<void()>); void begin(); void handleClient();
  void send(int, const char*, const char*); void send_P(int, const char*, const char*); String arg(const char*); };
