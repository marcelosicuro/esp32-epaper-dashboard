#!/bin/bash
# Prepara o simulador no macOS: SDL2, OpenSSL e um ambiente Python só para ele.
# Não mexe no ESPHome que você usa para gravar o aparelho.
set -e
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew não encontrado. Instale em https://brew.sh e rode de novo."
  exit 1
fi

if [ "$(uname -m)" != "arm64" ]; then
  echo "Aviso: este Mac não é Apple Silicon. O ESPHome procura o OpenSSL em /opt/homebrew."
  echo "Se a compilação falhar com 'openssl', crie o link: sudo ln -s /usr/local/opt/openssl /opt/homebrew/opt/openssl"
fi

for pacote in sdl2 openssl; do
  brew list "$pacote" >/dev/null 2>&1 || brew install "$pacote"
done

# O ESPHome atual exige Python 3.12 ou mais novo.
PY=""
for candidato in python3.14 python3.13 python3.12; do
  if command -v "$candidato" >/dev/null 2>&1; then PY="$candidato"; break; fi
done
if [ -z "$PY" ]; then
  brew install python@3.13
  PY="$(brew --prefix python@3.13)/bin/python3.13"
fi
echo "Usando $($PY --version)"

[ -d "$RAIZ/.venv-sim" ] || "$PY" -m venv "$RAIZ/.venv-sim"
"$RAIZ/.venv-sim/bin/pip" install -q --upgrade pip esphome pyyaml

if [ ! -s "$RAIZ/fonts/materialdesignicons-webfont.ttf" ]; then
  curl -L "https://raw.githubusercontent.com/Templarian/MaterialDesign-Webfont/master/fonts/materialdesignicons-webfont.ttf" \
       -o "$RAIZ/fonts/materialdesignicons-webfont.ttf"
fi

echo ""
echo "Pronto. Para abrir o simulador: simulador/rodar.sh"
