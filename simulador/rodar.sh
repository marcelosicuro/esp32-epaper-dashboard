#!/bin/bash
# Abre o simulador do painel numa janela. Veja o README (seção "Simulador no Mac").
set -e
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"

if [ ! -x "$RAIZ/.venv-sim/bin/python" ]; then
  echo "Ambiente do simulador não encontrado. Rode primeiro: simulador/instalar.sh"
  exit 1
fi

cd "$RAIZ/simulador"
exec "$RAIZ/.venv-sim/bin/python" rodar.py "$@"
