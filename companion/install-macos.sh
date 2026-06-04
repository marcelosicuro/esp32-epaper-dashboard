#!/bin/bash
# Instala o Companion como serviço macOS (auto-inicia no login)
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST="$HOME/Library/LaunchAgents/com.painel.companion.plist"
PYTHON="$(which python3)"

if [ ! -f "$SCRIPT_DIR/config.yaml" ]; then
  cp "$SCRIPT_DIR/config.yaml.example" "$SCRIPT_DIR/config.yaml"
  echo "✅ config.yaml criado — edite antes de continuar."
  exit 1
fi

pip3 install -q -r "$SCRIPT_DIR/requirements.txt"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>       <string>com.painel.companion</string>
  <key>ProgramArguments</key>
  <array>
    <string>$PYTHON</string>
    <string>$SCRIPT_DIR/server.py</string>
  </array>
  <key>RunAtLoad</key>   <true/>
  <key>KeepAlive</key>   <true/>
  <key>StandardOutPath</key> <string>/tmp/painel-companion.log</string>
  <key>StandardErrorPath</key><string>/tmp/painel-companion.log</string>
</dict>
</plist>
EOF

launchctl unload "$PLIST" 2>/dev/null || true
launchctl load -w "$PLIST"

echo ""
echo "✅ Companion instalado e iniciado."
echo "   Logs: tail -f /tmp/painel-companion.log"
echo "   Teste: curl http://localhost:8765/data.json"
echo ""
echo "Adicione ao secrets.yaml do ESPHome:"
echo "  companion_url: \"http://$(ipconfig getifaddr en0):8765\""
