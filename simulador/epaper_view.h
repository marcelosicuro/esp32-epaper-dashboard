#pragma once

// Visão "e-paper" para o simulador.
//
// No display real, COLOR_ON é tinta preta sobre papel branco. Numa janela SDL
// o padrão é o contrário (COLOR_ON = branco sobre fundo preto). Este adaptador
// recebe os pixels que a lambda do painel desenha e inverte as cores antes de
// repassar à janela, para o preview ficar igual ao que o e-paper mostra.

#include "esphome/components/display/display.h"

namespace painel_sim {

class EpaperView : public esphome::display::Display {
 public:
  explicit EpaperView(esphome::display::Display *target) : target_(target) {}

  void update() override {}

  esphome::display::DisplayType get_display_type() override {
    return esphome::display::DisplayType::DISPLAY_TYPE_BINARY;
  }

  void draw_pixel_at(int x, int y, esphome::Color color) override {
    // Igual ao driver Waveshare: qualquer cor "ligada" vira preto, o resto vira branco.
    target_->draw_pixel_at(x, y, color.is_on() ? esphome::Color(0, 0, 0) : esphome::Color(255, 255, 255));
  }

 protected:
  int get_width_internal() override { return target_->get_width(); }
  int get_height_internal() override { return target_->get_height(); }

  esphome::display::Display *target_;
};

}  // namespace painel_sim
