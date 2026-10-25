#pragma once
#include "esphome/components/display/display.h"

// Proxy de desenho: no e-Paper "ligado" = tinta preta sobre papel branco.
// Na janela SDL o padrão é o inverso, então este proxy mapeia as cores.
// Só implementa as chamadas usadas pelo lambda do painel.yaml.
struct EpPreview {
  esphome::display::Display &d;
  static esphome::Color map(esphome::Color c) {
    return (c.r | c.g | c.b) ? esphome::Color(0, 0, 0) : esphome::Color(255, 255, 255);
  }
  static esphome::Color ink() { return esphome::Color(0, 0, 0); }

  template<typename... A>
  void printf(int x, int y, esphome::display::BaseFont *f, esphome::display::TextAlign a, const char *fmt, A... args) {
    d.printf(x, y, f, ink(), a, fmt, args...);
  }
  template<typename... A>
  void printf(int x, int y, esphome::display::BaseFont *f, esphome::Color c, esphome::display::TextAlign a,
              const char *fmt, A... args) {
    d.printf(x, y, f, map(c), a, fmt, args...);
  }
  void strftime(int x, int y, esphome::display::BaseFont *f, esphome::display::TextAlign a, const char *fmt,
                esphome::ESPTime t) {
    d.strftime(x, y, f, ink(), a, fmt, t);
  }
  void line(int x1, int y1, int x2, int y2) { d.line(x1, y1, x2, y2, ink()); }
  void filled_rectangle(int x, int y, int w, int h) { d.filled_rectangle(x, y, w, h, ink()); }
};
