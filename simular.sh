#!/bin/bash
# Abre o simulador 800x480 do painel e-Paper no Mac (usa as APIs reais de clima/cotações).
cd "$(dirname "$0")"
.venv-sim/bin/python gerar_simulador.py && .venv-sim/bin/esphome run simulador.yaml --no-logs
